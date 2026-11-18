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
from upprepa import inventory, record, repeat


def create(method, project):
    if method not in ("kvantitativ", "kvalitativ"):
        raise ValueError("Välj kvantitativ eller kvalitativ.")
    project.mkdir()  # Ett befintligt projekt får aldrig skrivas över.
    try:
        shutil.copytree(HERE / "mallar" / "gemensamt", project / "underlag")
        shutil.copytree(HERE / "mallar" / method, project / "underlag", dirs_exist_ok=True)
        (project / "korningar").mkdir()
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


def container(work, image, build=False):
    if not re.fullmatch(r"[a-z0-9][a-z0-9./:_-]*@sha256:[a-f0-9]{64}", image):
        raise ValueError("Ogiltig låst labbavbildning.")
    podman = os.environ.get("FORSKAROS_PODMAN", "podman")
    access = "Z" if build else "ro,Z"
    cmd = [podman, "run", "--rm", "--network=none", "--userns=keep-id",
           "-v", f"{work}:/arbete:{access}", "-w", "/arbete",
           "-e", f"FORSKAROS_KORNINGSLABB={image}", image, "python", "-I", "upprepa.py"]
    if build:
        cmd.append("--bygg")
    subprocess.run(cmd, check=True)


def run(project, lab=False):
    inputs = project / "underlag"
    runs = project / "korningar"
    if runs.is_symlink() or not runs.is_dir():
        raise ValueError("Välj en projektmapp som innehåller underlag och korningar.")
    inventory(inputs)
    name = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ") + "-" + uuid4().hex[:10]
    with tempfile.TemporaryDirectory(prefix=".arbete-", dir=runs) as tmp:
        # Publicera först efter lyckad analys och rapportbygge.
        work = Path(tmp) / "korning"
        work.mkdir()
        shutil.copytree(inputs, work / "underlag", symlinks=True)
        inventory(work / "underlag")
        shutil.copyfile(HERE / "upprepa.py", work / "upprepa.py")
        if lab:
            container(work, pinned_image(), build=True)
        else:
            record(work)
        work.rename(runs / name)
    return runs / name


def verify(folder):
    manifest = json.loads((folder / "korning.json").read_text(encoding="utf-8"))
    if manifest.get("labb"):
        container(folder, manifest["labb"])
    else:
        repeat(folder)


def main():
    parser = argparse.ArgumentParser(description="Forskningsprojekt med flyttbara körningar.")
    commands = parser.add_subparsers(dest="command")
    new = commands.add_parser("skapa")
    new.add_argument("metod", choices=["kvantitativ", "kvalitativ"])
    new.add_argument("mapp", type=Path)
    start = commands.add_parser("kör")
    start.add_argument("mapp", type=Path)
    start.add_argument("--labb", action="store_true", help="Kör med ForskarOS-labbets låsta avbildning.")
    commands.add_parser("upprepa").add_argument("mapp", type=Path)
    args = parser.parse_args()
    if args.command == "skapa":
        print(create(args.metod, args.mapp.resolve()))
    elif args.command == "kör":
        print(run(args.mapp.resolve(), args.labb))
    elif args.command == "upprepa":
        verify(args.mapp.resolve())
    else:
        from skrivbord import window
        window(create, run, verify)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
