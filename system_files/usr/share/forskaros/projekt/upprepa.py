"""Återskapa en ForskarOS-körning: python3 upprepa.py (i valfri arbetskatalog)."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile


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


def record(root, image=None):
    inputs = inventory(root / "underlag")
    env = environment()
    with_evidence = (root / "belagg.py").is_file()
    build(root, with_evidence)
    compare("Underlag ändrat av analysen", inputs, inventory(root / "underlag"))
    manifest = {"format": 1, "miljö": env, "labb": image, "underlag": inputs,
                "resultat": inventory(root / "resultat"), "upprepa.py": checksum(root / "upprepa.py")}
    if with_evidence:
        manifest["belagg.py"] = checksum(root / "belagg.py")
    (root / "korning.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def repeat(root):
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
        elif not sys.argv[1:]:
            repeat(root)
        else:
            raise ValueError("Använd python3 upprepa.py för att verifiera körningen.")
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
