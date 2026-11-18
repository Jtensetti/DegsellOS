#!/usr/bin/env python3
"""Paketerar en ForskarOS-disk som en färdig UTM-maskin (.utm.zip).

En .utm är en mapp med config.plist och disken i Data/. Vi skriver inte
config.plist från grunden: formatet är UTM:s eget. I stället utgår vi från en
QEMU-mall som UTM själv har skapat och byter bara ut:
  - namn, beskrivning och UUID
  - disken (första disken av typen Disk)
  - minne och processorer, om nycklarna finns
  - nätverkskortets MAC-adress (ny för varje bygge)

  python3 scripts/paketera_utm.py MALL.plist DISK.qcow2 UT.utm.zip [--minne 8192 --cpu 4]
"""
import argparse
import plistlib
import secrets
import os
import tempfile
import uuid
import zipfile
from pathlib import Path


def random_mac():
    # Lokalt administrerad unicast-adress.
    b = [0x02] + [secrets.randbelow(256) for _ in range(5)]
    return ":".join(f"{x:02X}" for x in b)


def adapt(config: dict, disk_name: str, memory: int, cpus: int) -> dict:
    if config.get("Backend") != "QEMU" or config.get("System", {}).get("Architecture") != "aarch64":
        raise SystemExit("Välj en QEMU-maskin för ARM64 i UTM.")
    if config.get("ConfigurationVersion") != 4:
        raise SystemExit("Välj en QEMU-mall med ConfigurationVersion 4.")
    if min(memory, cpus) < 1:
        raise SystemExit("Ange positivt minne och minst en processorkärna.")
    if config.get("Information", {}).get("IconCustom") or config.get("QEMU", {}).get("TPMDevice"):
        raise SystemExit("Välj en mall med inbyggd ikon och utan TPM. Båda kan kräva extra filer.")
    info = config.setdefault("Information", {})
    info["Name"] = "ForskarOS"
    info["UUID"] = str(uuid.uuid4()).upper()
    info["Notes"] = ("ForskarOS – ett forskningsorienterat operativsystem. "
                     "Inloggning: forskare / forskare (lösenordet måste bytas vid första inloggningen).")

    drives = config.get("Drive", [])
    disks = [d for d in drives if d.get("ImageType") == "Disk" and d.get("ImageName") and not d.get("ReadOnly", False)]
    if len(disks) != 1 or any(d is not disks[0] and d.get("ImageType") != "CD" for d in drives):
        raise SystemExit("Mallen måste ha en skrivbar hårddisk och får bara ha cd-enheter därutöver.")
    disks[0]["ImageName"] = disk_name
    disks[0]["Identifier"] = str(uuid.uuid4()).upper()
    # Andra diskar (t.ex. installations-ISO) tas bort.
    config["Drive"] = disks

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

    out = Path(a.ut)
    if out.resolve() in (disk.resolve(), Path(a.mall).resolve()):
        raise SystemExit("Spara zip-paketet under ett annat namn än originalfilerna.")
    # qcow2-filen är redan komprimerad. Strömma den direkt till ZIP64 utan
    # en extra kopia på flera GiB och publicera först när arkivet är stängt.
    with tempfile.NamedTemporaryFile(dir=out.parent, suffix=".zip", delete=False) as tmp:
        pending = Path(tmp.name)
    try:
        with zipfile.ZipFile(pending, "w", allowZip64=True) as z:
            z.writestr("ForskarOS.utm/config.plist", plistlib.dumps(config))
            z.write(disk, arcname=f"ForskarOS.utm/Data/{disk.name}")
        os.replace(pending, out)
    finally:
        pending.unlink(missing_ok=True)
    print(f"Skapade {a.ut}")


if __name__ == "__main__":
    main()
