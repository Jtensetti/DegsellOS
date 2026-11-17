#!/usr/bin/env python3
"""Paketerar en ForskarOS-disk som en färdig UTM-maskin (.utm.zip).

En .utm är en mapp med config.plist och disken i Data/. Vi skriver inte
config.plist från grunden: formatet är UTM:s eget. I stället utgår vi från en
mall som UTM själv skapat (vm/utm/config.plist) och byter bara ut:
  - namn, beskrivning och UUID
  - disken (första disken av typen Disk)
  - minne och processorer, om nycklarna finns
  - nätverkskortets MAC-adress (ny för varje bygge)

  python3 scripts/paketera_utm.py MALL.plist DISK.qcow2 UT.utm.zip [--minne 8192 --cpu 4]
"""
import argparse
import plistlib
import random
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path


def random_mac():
    # Lokalt administrerad unicast-adress.
    b = [0x02] + [random.randint(0, 255) for _ in range(5)]
    return ":".join(f"{x:02X}" for x in b)


def adapt(config: dict, disk_name: str, memory: int, cpus: int) -> dict:
    info = config.setdefault("Information", {})
    info["Name"] = "ForskarOS"
    info["UUID"] = str(uuid.uuid4()).upper()
    info["Notes"] = ("ForskarOS – ett forskningsorienterat operativsystem. "
                     "Inloggning: forskare / forskare (lösenordet måste bytas vid första inloggningen).")

    drives = config.get("Drive", [])
    disks = [d for d in drives if d.get("ImageType", "Disk") == "Disk" and not d.get("ReadOnly", False)]
    if not disks:
        raise SystemExit("Mallen har ingen disk. Skapa mallen med en hårddisk i UTM.")
    disks[0]["ImageName"] = disk_name
    disks[0]["Identifier"] = str(uuid.uuid4()).upper()
    # Andra diskar (t.ex. installations-ISO) tas bort.
    config["Drive"] = [d for d in drives if d is disks[0]]

    system = config.get("System", {})
    for key in ("MemorySize", "Memory"):
        if key in system:
            system[key] = memory
    for key in ("CPUCount", "CPUs"):
        if key in system:
            system[key] = cpus

    for net in config.get("Network", []):
        if "MacAddress" in net:
            net["MacAddress"] = random_mac()
    return config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mall")
    ap.add_argument("disk")
    ap.add_argument("ut")
    ap.add_argument("--minne", type=int, default=8192)
    ap.add_argument("--cpu", type=int, default=4)
    a = ap.parse_args()

    config = plistlib.loads(Path(a.mall).read_bytes())
    disk = Path(a.disk)
    config = adapt(config, disk.name, a.minne, a.cpu)

    with tempfile.TemporaryDirectory() as tmp:
        bundle = Path(tmp) / "ForskarOS.utm"
        (bundle / "Data").mkdir(parents=True)
        (bundle / "config.plist").write_bytes(plistlib.dumps(config))
        shutil.copy(disk, bundle / "Data" / disk.name)
        out = Path(a.ut)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
            for f in sorted(bundle.rglob("*")):
                z.write(f, f.relative_to(tmp))
    print(f"Skapade {a.ut}")


if __name__ == "__main__":
    main()
