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
from belagg import approve, detail, inspect, locked
from upprepa import checksum, coverage, inventory, log_verification, record, sandbox, sandbox_probe
from paket import write_crate

METODER = {
    "kvantitativ": "Observationer i en tabell, till exempel från Calc. Jämför grupper eller villkor.",
    "kvalitativ": "Kodade utdrag ur intervjuer eller dokument, till exempel från Taguette.",
    "källtolkning": "Jämför vad två skriftliga källor säger om samma händelse.",
}

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


def link(project, fråga=None, hypotes=None, medarbetare=None):
    """Koppla projektet till en forskningsfråga och hypotes i forskningsmappen."""
    path = project / "projekt.json"
    manifest = domain(project)
    for key, value in (("fråga", fråga), ("hypotes", hypotes)):
        if value is not None:
            if value:
                manifest[key] = value.removesuffix(".md")
            else:
                manifest.pop(key, None)
    if medarbetare is not None:
        names = [n.strip() for n in (medarbetare.split(",") if isinstance(medarbetare, str) else medarbetare)]
        manifest["medarbetare"] = [n for n in names if n]
        if not manifest["medarbetare"]:
            del manifest["medarbetare"]
    if not path.exists():
        manifest["id"] = str(uuid4())
    tmp = path.with_name(".projekt.json.tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    sync(project)
    return manifest


def sync(project, state=None):
    """Skriv projektets läge till forskningsmappen om projektet är kopplat till en fråga."""
    from forskningsmapp import sync as write_note
    from oversikt import overview
    try:
        manifest = domain(project)
        if manifest.get("fråga"):
            return write_note(project, state or overview(project, domain), manifest)
    except (OSError, ValueError, KeyError):
        pass  # Forskningsmappen är ett tillägg. Projektet fungerar utan den.
    return False


def create(method, project, protection="öppen", fråga=None, hypotes=None, medarbetare=None):
    if method not in METODER:
        raise ValueError("Välj en av metoderna " + ", ".join(METODER) + ".")
    if protection not in SKYDD:
        raise ValueError("Välj skyddsnivå öppen eller skyddad.")
    project.mkdir()  # Ett befintligt projekt får aldrig skrivas över.
    try:
        templates = HERE / "mallar"
        inputs = project / "underlag"
        shutil.copytree(templates / "gemensamt", inputs)
        if method in ("kvantitativ", "kvalitativ"):
            shutil.copytree(templates / "tabell", inputs, dirs_exist_ok=True)
        shutil.copytree(templates / method, inputs, dirs_exist_ok=True)
        (project / "korningar").mkdir()
        manifest = {"format": 1, "id": str(uuid4()), "titel": project.name, "metod": method,
                    "skydd": protection, "skapad": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        (project / "projekt.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8")
    except BaseException:
        shutil.rmtree(project)
        raise
    if fråga or medarbetare:
        link(project, fråga, hypotes, medarbetare)
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
        from forskningsmapp import prediction
        earlier = [r for r in runs.iterdir() if not r.name.startswith(".") and (r / "korning.json").is_file()]
        text = prediction(manifest, earlier=earlier)
        if text:
            (work / "forutsagelse.md").write_text(text, encoding="utf-8")
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
    sync(project)
    return runs / name


def verify(folder):
    # Även äldre körprogram uppdaterar loggen och paketet en i taget.
    try:
        with locked(folder):
            _verify_locked(folder)
    finally:
        project = folder.parent.parent
        if (project / "underlag").is_dir():
            sync(project)


def _verify_locked(folder):
    manifest = json.loads((folder / "korning.json").read_text(encoding="utf-8"))
    try:
        runner = folder / "upprepa.py"
        if not runner.is_file() or checksum(runner) != manifest["upprepa.py"]:
            detail = "Körprogram avviker: upprepa.py"
            log_verification(folder, "avviker", detail)
            raise ValueError(detail)
        if manifest.get("labb"):
            container(folder, manifest["labb"])
        else:
            # upprepa.py startar själv sandlådan för körningar från skyddade projekt.
            result = subprocess.run([sys.executable, "-IB", str(runner)], capture_output=True, text=True)
            print(result.stdout, end="")
            if result.returncode:
                raise ValueError((result.stderr.strip() or "Upprepningen misslyckades.").splitlines()[-1])
    finally:
        if (folder / "ro-crate-metadata.json").exists() and os.access(folder, os.W_OK):
            write_crate(folder, verification_only=True)


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
    new.add_argument("metod", choices=METODER)
    new.add_argument("mapp", type=Path)
    new.add_argument("--skydd", choices=list(SKYDD), default="öppen",
                     help="skyddad: analysen körs utan nätverk och utan hemkatalog, annars inte alls.")
    new.add_argument("--fråga", help="Forskningsfrågan i forskningsmappen, t.ex. '01 RIKTNING/Min fråga'.")
    new.add_argument("--hypotes", help="Hypotesen som projektet prövar, t.ex. '02 HYPOTESER/Hypotes 2026-11-19'.")
    new.add_argument("--medarbetare", help="Namn, åtskilda med komma.")
    tie = commands.add_parser("koppla", help="Koppla projektet till en forskningsfråga i forskningsmappen.")
    tie.add_argument("mapp", type=Path)
    tie.add_argument("--fråga", help="Tom sträng tar bort kopplingen.")
    tie.add_argument("--hypotes")
    tie.add_argument("--medarbetare")
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
        print(create(args.metod, args.mapp.resolve(), args.skydd, args.fråga, args.hypotes, args.medarbetare))
    elif args.command == "koppla":
        manifest = link(args.mapp.resolve(), args.fråga, args.hypotes, args.medarbetare)
        print(manifest.get("fråga") or "Projektet är inte kopplat till någon forskningsfråga.")
    elif args.command == "status":
        print(status(args.mapp.resolve()))
    elif args.command == "paketera":
        folder = args.mapp.resolve()
        project = folder.parent.parent
        with locked(folder):
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
        # Utan underkommando öppnas skrivbordsappen.
        os.execv(sys.executable, [sys.executable, "-I", str(HERE / "app.py")])


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
