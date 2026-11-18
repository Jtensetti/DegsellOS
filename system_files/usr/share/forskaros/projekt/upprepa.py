"""Återskapa en ForskarOS-körning: python3 upprepa.py (i valfri arbetskatalog).

En körning från ett skyddat projekt upprepas i en bubblewrap-sandlåda utan
nätverk och utan hemkatalog. Finns inte bubblewrap avbryts upprepningen, om
du inte uttryckligen väljer python3 upprepa.py --utan-skydd.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile


# Mappar som döljs i sandlådan. /run döljs eftersom en skrivskyddad montering
# inte hindrar en process från att ansluta till systemets och sessionens uttag.
DOLDA = ("/home", "/var/home", "/root", "/run", "/tmp", "/var/tmp", "/mnt", "/var/mnt",
         "/media", "/srv")


def sandbox(work, argv):
    """Kör argv utan nätverk och utan åtkomst till hemkataloger. Bara work är skrivbar."""
    # FORSKAROS_BWRAP pekar ut en annan bubblewrap, t.ex. i tester av vägran.
    bwrap = os.environ.get("FORSKAROS_BWRAP") or shutil.which("bwrap")
    if not bwrap:
        raise ValueError("bubblewrap (bwrap) saknas, så sandlådan kan inte startas.")
    work = Path(work).resolve()
    cmd = [bwrap, "--unshare-all", "--die-with-parent", "--new-session", "--clearenv",
           "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc"]
    hidden = []
    for name in DOLDA:
        path = Path(name)
        if path.is_dir() and not path.is_symlink() and not any(path.is_relative_to(h) for h in hidden):
            hidden.append(path)
            cmd += ["--tmpfs", name]
    cmd += ["--bind", str(work), str(work), "--chdir", str(work),
            "--setenv", "PATH", "/usr/local/bin:/usr/bin:/bin", "--setenv", "HOME", str(work),
            "--setenv", "LANG", "C.UTF-8", "--setenv", "FORSKAROS_SANDLADA", "bubblewrap"]
    return cmd + ["--", *argv]


def sandbox_probe(work):
    """Kontrollera att sandlådan faktiskt kan startas innan analysen körs."""
    result = subprocess.run(sandbox(work, ["true"]), capture_output=True, text=True)
    if result.returncode:
        reason = (result.stderr.strip() or f"avslutningskod {result.returncode}").splitlines()[-1]
        raise ValueError(f"Sandlådan kunde inte startas ({reason}).")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory(folder):
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError(f"Vanlig mapp saknas: {folder}")
    hashes = {}
    for path in sorted(folder.rglob("*")):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"Endast vanliga filer och mappar kan följa med: {path}")
        if path.is_file():
            hashes[path.relative_to(folder).as_posix()] = checksum(path)
    return hashes


def compare(label, expected, actual):
    changed = sorted(k for k in expected.keys() | actual.keys() if expected.get(k) != actual.get(k))
    if changed:
        raise ValueError(f"{label} avviker: {', '.join(changed)}")


def execute(args, cwd):
    result = subprocess.run(args, cwd=cwd, stderr=subprocess.PIPE, text=True, errors="replace")
    if result.returncode:
        detail = result.stderr.strip() or f"Avslutningskod {result.returncode}"
        raise ValueError(detail.splitlines()[-1] if args[0] == sys.executable else detail[-1600:])


def build(root, with_evidence):
    output = root / "resultat"
    output.mkdir()
    # Analysen får arbeta i sin egen kopia av underlaget.
    execute([sys.executable, "-IB", "analys.py", str(output)], root / "underlag")
    cmd = ["pandoc", "underlag/manus.md", "--standalone", "--embed-resources",
           "--resource-path=.:underlag", "--citeproc", "--bibliography=underlag/kallor.bib",
           "--fail-if-warnings", "--output=resultat/rapport.html"]
    if with_evidence:
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from belagg import appendix, inspect
        claims = inspect(root / "underlag")
        if claims:
            with tempfile.TemporaryDirectory() as tmp:
                snippet = Path(tmp) / "belagg.html"
                snippet.write_text(appendix(claims), encoding="utf-8")
                execute(cmd + ["--include-after-body", str(snippet)], root)
            return
    execute(cmd, root)


def environment():
    version = subprocess.check_output(["pandoc", "--version"], text=True).splitlines()[0]
    return {"python": platform.python_version(), "pandoc": version, "arkitektur": platform.machine()}


def protection():
    """Hur den här processen är isolerad, enligt den som startade den."""
    value = os.environ.get("FORSKAROS_SKYDD")
    return json.loads(value) if value else None


def record(root, image=None):
    inputs = inventory(root / "underlag")
    env = environment()
    with_evidence = (root / "belagg.py").is_file()
    started = now()
    build(root, with_evidence)
    compare("Underlag ändrat av analysen", inputs, inventory(root / "underlag"))
    manifest = {"format": 1, "miljö": env, "labb": image, "underlag": inputs,
                "resultat": inventory(root / "resultat"), "upprepa.py": checksum(root / "upprepa.py"),
                "start": started, "slut": now(), "skydd": protection()}
    if with_evidence:
        manifest["belagg.py"] = checksum(root / "belagg.py")
    (root / "korning.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def log_verification(root, outcome, detail):
    """Spara varje upprepning, även misslyckade, så att täckningsgraden stämmer."""
    path = root / "verifieringar.json"
    try:
        entries = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        entries.append({"tid": now(), "utfall": outcome, "detalj": detail,
                        "miljö": environment(), "system": platform.system() + " " + platform.release(),
                        "skydd": os.environ.get("FORSKAROS_SANDLADA") or ("podman" if os.environ.get("FORSKAROS_KORNINGSLABB") else None)})
        tmp = path.with_name(".verifieringar.json.tmp")
        tmp.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
    except OSError as error:
        print(f"Upprepningen kunde inte loggas i {path}: {error}", file=sys.stderr)


def coverage(root):
    """Dokumenterad, återkörbar eller återkörd, med det som visar nivån."""
    manifest = json.loads((root / "korning.json").read_text(encoding="utf-8"))
    path = root / "verifieringar.json"
    entries = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    same = [e for e in entries if e["utfall"] == "samma"]
    if same:
        when = same[-1]["tid"][:16].replace("T", " ") + " UTC"
        count = "1 upprepning" if len(same) == 1 else f"{len(same)} upprepningar"
        return "Återkörd", f"{count} gav samma SHA-256, senast {when}"
    shield = manifest.get("skydd") or {}
    if manifest.get("labb") or shield.get("nätverk") == "avstängt":
        return "Återkörbar", "Körd utan nätverk och utan åtkomst utanför körningsmappen"
    return "Dokumenterad", "Underlag, resultat och programversioner är registrerade"


def repeat(root):
    try:
        _repeat(root)
    except ValueError as error:
        log_verification(root, "avviker", str(error))
        raise
    log_verification(root, "samma", "Alla resultat har samma SHA-256.")


def _repeat(root):
    manifest = json.loads((root / "korning.json").read_text(encoding="utf-8"))
    if manifest.get("format") != 1:
        raise ValueError("Okänt format på korning.json.")
    compare("Körprogram", {"upprepa.py": manifest["upprepa.py"]}, {"upprepa.py": checksum(root / "upprepa.py")})
    if "belagg.py" in manifest:
        compare("Beläggsprogram", {"belagg.py": manifest["belagg.py"]}, {"belagg.py": checksum(root / "belagg.py")})
    compare("Underlag", manifest["underlag"], inventory(root / "underlag"))
    compare("Sparade resultat", manifest["resultat"], inventory(root / "resultat"))
    env = environment()
    if env != manifest["miljö"]:
        print(f"Annan analysmiljö. Ursprungligen {manifest['miljö']}. Nu {env}.", file=sys.stderr)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copytree(root / "underlag", work / "underlag", symlinks=True)
        build(work, "belagg.py" in manifest)
        compare("Återskapade resultat", manifest["resultat"], inventory(work / "resultat"))
    print("Återskapad från underlaget. Alla resultat har samma SHA-256.")


if __name__ == "__main__":
    try:
        root = Path(__file__).resolve().parent
        if sys.argv[1:] == ["--bygg"]:
            record(root, os.environ.get("FORSKAROS_KORNINGSLABB"))
        elif sys.argv[1:] in ([], ["--utan-skydd"]):
            manifest = json.loads((root / "korning.json").read_text(encoding="utf-8"))
            protected = (manifest.get("skydd") or {}).get("nivå") == "skyddad"
            isolated = os.environ.get("FORSKAROS_SANDLADA") or os.environ.get("FORSKAROS_KORNINGSLABB")
            if protected and not isolated and sys.argv[1:] != ["--utan-skydd"]:
                if not (os.environ.get("FORSKAROS_BWRAP") or shutil.which("bwrap")):
                    raise ValueError("Körningen kommer från ett skyddat projekt och ska upprepas utan nätverk "
                                     "och utan hemkatalog. bubblewrap saknas här. Kör python3 upprepa.py "
                                     "--utan-skydd för att ändå upprepa den utan skydd.")
                sandbox_probe(root)
                sys.exit(subprocess.run(sandbox(root, [sys.executable, "-IB", str(root / "upprepa.py")])).returncode)
            repeat(root)
        else:
            raise ValueError("Använd python3 upprepa.py för att verifiera körningen.")
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
