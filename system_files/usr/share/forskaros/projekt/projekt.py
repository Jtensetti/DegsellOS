import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from uuid import uuid4


HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
from belagg import approve, detail, inspect
from upprepa import checksum, coverage, inventory, record, sandbox, sandbox_probe
from paket import write_crate

SKYDD = {
    "öppen": "Öppet material. Analysen körs som vanligt.",
    "skyddad": "Skyddat material, t.ex. intervjuer eller personuppgifter. Analysen körs utan nätverk "
               "och utan åtkomst till hemkatalogen, annars inte alls.",
}


def domain(project):
    """Projektets manifest. Äldre projekt utan manifest behandlas som öppna."""
    path = project / "projekt.json"
    if not path.exists():
        return {"format": 1, "id": None, "titel": project.name, "skydd": "öppen"}
    if path.is_symlink():
        raise ValueError("projekt.json ska vara en vanlig fil.")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("format") != 1 or manifest.get("skydd") not in SKYDD:
        raise ValueError("projekt.json har okänt format eller skyddsnivå (öppen eller skyddad).")
    return manifest


def create(method, project, protection="öppen"):
    if method not in ("kvantitativ", "kvalitativ"):
        raise ValueError("Välj kvantitativ eller kvalitativ.")
    if protection not in SKYDD:
        raise ValueError("Välj skyddsnivå öppen eller skyddad.")
    project.mkdir()  # Ett befintligt projekt får aldrig skrivas över.
    try:
        shutil.copytree(HERE / "mallar" / "gemensamt", project / "underlag")
        shutil.copytree(HERE / "mallar" / method, project / "underlag", dirs_exist_ok=True)
        (project / "korningar").mkdir()
        manifest = {"format": 1, "id": str(uuid4()), "titel": project.name, "metod": method,
                    "skydd": protection, "skapad": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        (project / "projekt.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8")
    except BaseException:
        shutil.rmtree(project)
        raise
    return project


def pinned_image():
    image = os.environ.get("FORSKAROS_LABB", "ghcr.io/jtensetti/researchos-labb:latest")
    podman = os.environ.get("FORSKAROS_PODMAN", "podman")
    if subprocess.run([podman, "image", "exists", image]).returncode:
        subprocess.run([podman, "pull", image], check=True)
    digests = json.loads(subprocess.check_output([podman, "image", "inspect", image], text=True))[0]["RepoDigests"]
    if not digests:
        raise ValueError("Labbavbildningen saknar publicerad digest.")
    return digests[0]


def container(work, image, build=False, shield=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9./:_-]*@sha256:[a-f0-9]{64}", image):
        raise ValueError("Ogiltig låst labbavbildning.")
    podman = os.environ.get("FORSKAROS_PODMAN", "podman")
    # Upprepningen skriver sin logg i körningsmappen.
    cmd = [podman, "run", "--rm", "--network=none", "--userns=keep-id",
           "-v", f"{work}:/arbete:Z", "-w", "/arbete",
           "-e", f"FORSKAROS_KORNINGSLABB={image}"]
    if shield:
        cmd += ["-e", "FORSKAROS_SKYDD=" + json.dumps(shield, ensure_ascii=False)]
    cmd += [image, "python", "-I", "upprepa.py"]
    if build:
        cmd.append("--bygg")
    subprocess.run(cmd, check=True)


def shield_for(manifest, lab):
    """Isoleringen som körningen faktiskt får. Sparas i korning.json."""
    if lab:
        return {"nivå": manifest["skydd"], "mekanism": "podman --network=none", "nätverk": "avstängt",
                "hemkatalog": "ej monterad"}
    if manifest["skydd"] == "skyddad":
        binary = os.environ.get("FORSKAROS_BWRAP") or shutil.which("bwrap") or "bwrap"
        version = subprocess.run([binary, "--version"], capture_output=True, text=True).stdout.strip()
        return {"nivå": "skyddad", "mekanism": version or "bubblewrap", "nätverk": "avstängt",
                "hemkatalog": "dold"}
    return {"nivå": "öppen", "mekanism": None, "nätverk": "tillgängligt", "hemkatalog": "tillgänglig"}


def run(project, lab=False):
    inputs = project / "underlag"
    runs = project / "korningar"
    if runs.is_symlink() or not runs.is_dir():
        raise ValueError("Välj en projektmapp som innehåller underlag och korningar.")
    manifest = domain(project)
    inventory(inputs)
    name = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ") + "-" + uuid4().hex[:10]
    with tempfile.TemporaryDirectory(prefix=".arbete-", dir=runs) as tmp:
        # Publicera först efter lyckad analys och rapportbygge.
        work = Path(tmp) / "korning"
        work.mkdir()
        shutil.copytree(inputs, work / "underlag", symlinks=True)
        inventory(work / "underlag")
        for program in ("upprepa.py", "belagg.py"):
            shutil.copyfile(HERE / program, work / program)
        shield = shield_for(manifest, lab)
        if lab:
            container(work, pinned_image(), build=True, shield=shield)
        elif manifest["skydd"] == "skyddad":
            try:
                sandbox_probe(work)
            except ValueError as error:
                raise ValueError(f"{error} Projektet är skyddat, så ForskarOS kör inte analysen utan skydd. "
                                 "Använd det versionslåsta labbet eller en dator där bubblewrap fungerar.") from None
            env = {"FORSKAROS_SKYDD": json.dumps(shield, ensure_ascii=False)}
            cmd = sandbox(work, [sys.executable, "-IB", str(work / "upprepa.py"), "--bygg"])
            cmd[cmd.index("--"):cmd.index("--")] = ["--setenv", "FORSKAROS_SKYDD", env["FORSKAROS_SKYDD"]]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode:
                raise ValueError((result.stderr.strip() or "Analysen misslyckades i sandlådan.").splitlines()[-1])
        else:
            os.environ["FORSKAROS_SKYDD"] = json.dumps(shield, ensure_ascii=False)
            try:
                record(work)
            finally:
                os.environ.pop("FORSKAROS_SKYDD", None)
        write_crate(work, manifest)
        work.rename(runs / name)
    return runs / name


def verify(folder):
    manifest = json.loads((folder / "korning.json").read_text(encoding="utf-8"))
    if checksum(folder / "upprepa.py") != manifest["upprepa.py"]:
        raise ValueError("Körprogram avviker: upprepa.py")
    if manifest.get("labb"):
        container(folder, manifest["labb"])
    else:
        # upprepa.py startar själv sandlådan för körningar från skyddade projekt.
        result = subprocess.run([sys.executable, "-IB", str(folder / "upprepa.py")], capture_output=True, text=True)
        print(result.stdout, end="")
        if result.returncode:
            raise ValueError((result.stderr.strip() or "Upprepningen misslyckades.").splitlines()[-1])
    project = folder.parent.parent
    if (folder / "ro-crate-metadata.json").exists() and os.access(folder, os.W_OK):
        write_crate(folder, domain(project) if (project / "underlag").is_dir() else None)


def status(project):
    manifest = domain(project)
    lines = [f'{manifest["titel"]} · {manifest["skydd"]}', SKYDD[manifest["skydd"]]]
    runs = sorted(p for p in (project / "korningar").iterdir()
                  if not p.name.startswith(".") and (p / "korning.json").is_file())
    if not runs:
        lines.append("Inga körningar än.")
    for folder in runs:
        level, why = coverage(folder)
        lines.append(f"{folder.name} · {level} · {why}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Forskningsprojekt med flyttbara körningar.")
    commands = parser.add_subparsers(dest="command")
    new = commands.add_parser("skapa")
    new.add_argument("metod", choices=["kvantitativ", "kvalitativ"])
    new.add_argument("mapp", type=Path)
    new.add_argument("--skydd", choices=list(SKYDD), default="öppen",
                     help="skyddad: analysen körs utan nätverk och utan hemkatalog, annars inte alls.")
    commands.add_parser("status", help="Visa skyddsnivå och körningarnas täckningsgrad.").add_argument("mapp", type=Path)
    pack = commands.add_parser("paketera", help="Skriv om körningens RO-Crate-metadata.")
    pack.add_argument("mapp", type=Path)
    start = commands.add_parser("kör")
    start.add_argument("mapp", type=Path)
    start.add_argument("--labb", action="store_true", help="Kör med ForskarOS-labbets låsta avbildning.")
    commands.add_parser("upprepa").add_argument("mapp", type=Path)
    evidence = commands.add_parser("belägg", help="Visa manusets påståenden och deras aktuella underlag.")
    evidence.add_argument("mapp", type=Path)
    evidence.add_argument("id", nargs="?")
    review = commands.add_parser("granska", help="Bekräfta det underlag som du just har läst.")
    review.add_argument("mapp", type=Path)
    review.add_argument("id")
    review.add_argument("--avtryck", required=True, help="Avtrycket från belägg-kommandot.")
    args = parser.parse_args()
    if args.command == "skapa":
        print(create(args.metod, args.mapp.resolve(), args.skydd))
    elif args.command == "status":
        print(status(args.mapp.resolve()))
    elif args.command == "paketera":
        folder = args.mapp.resolve()
        project = folder.parent.parent
        print(write_crate(folder, domain(project) if (project / "underlag").is_dir() else None))
    elif args.command == "kör":
        print(run(args.mapp.resolve(), args.labb))
    elif args.command == "upprepa":
        verify(args.mapp.resolve())
    elif args.command in ("belägg", "granska"):
        folder = args.mapp.resolve() / "underlag"
        if not folder.is_dir():
            raise ValueError("Välj en projektmapp med underlag.")
        if args.command == "granska":
            approve(folder, args.id, args.avtryck)
            print("Granskningen är sparad.")
        else:
            claims = inspect(folder)
            if args.id:
                if args.id not in claims:
                    raise ValueError(f"Okänt påstående: {args.id}")
                claim = claims[args.id]
                print(detail(claim))
                print("Avtryck:", claim["avtryck"])
            else:
                for key, claim in claims.items():
                    print(f'{key} · {claim["status"]} · {claim["text"]}')
                if not claims:
                    print("Manuset har inga länkade påståenden.")
    else:
        # Utan kommando öppnas appen ForskarOS. Allt nedan finns kvar på kommandoraden.
        os.execv(sys.executable, [sys.executable, "-I", str(HERE / "app.py")])


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
