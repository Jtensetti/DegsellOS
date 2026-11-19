"""Testar UTM-paketeringen mot en syntetisk mall med UTM:s struktur."""
import plistlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

template = {
    "Backend": "QEMU",
    "ConfigurationVersion": 4,
    "Information": {"Name": "Mall", "UUID": "AAAA", "Icon": "linux", "IconCustom": False},
    "System": {"Architecture": "aarch64", "MemorySize": 2048, "CPUCount": 0},
    "Drive": [
        {"ImageName": "gammal.qcow2", "ImageType": "Disk", "Interface": "VirtIO", "Identifier": "X", "ReadOnly": False},
        {"ImageType": "CD", "Interface": "USB", "Identifier": "Y", "ReadOnly": True},
    ],
    "Network": [{"Mode": "Shared", "Hardware": "virtio-net-pci", "MacAddress": "AA:BB:CC:DD:EE:FF"}],
    "Sharing": {"ClipboardSharing": True, "DirectoryShareMode": "VirtFS"},
}

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    (tmp / "config.plist").write_bytes(plistlib.dumps(template))
    disk = tmp / "DegsellOS-2027.1-arm64.qcow2"
    disk.write_bytes(b"QFI\xfb" + b"\0" * 1020)
    out = tmp / "DegsellOS.utm.zip"
    subprocess.run([sys.executable, str(ROOT / "scripts/paketera_utm.py"), str(tmp / "config.plist"), str(disk), str(out)],
                   check=True, capture_output=True)

    with zipfile.ZipFile(out) as z:
        names = set(z.namelist())
        assert "DegsellOS.utm/config.plist" in names, names
        assert "DegsellOS.utm/Data/DegsellOS-2027.1-arm64.qcow2" in names, names
        cfg = plistlib.loads(z.read("DegsellOS.utm/config.plist"))

    assert cfg["Information"]["Name"] == "DegsellOS"
    assert cfg["Information"]["UUID"] != "AAAA"
    assert "forskare / forskare" in cfg["Information"]["Notes"]
    assert len(cfg["Drive"]) == 1, "installations-cd:n ska tas bort"
    assert cfg["Drive"][0]["ImageName"] == "DegsellOS-2027.1-arm64.qcow2"
    assert cfg["System"]["MemorySize"] == 8192 and cfg["System"]["CPUCount"] == 4
    assert cfg["Network"][0]["MacAddress"] != "AA:BB:CC:DD:EE:FF"
    assert cfg["Sharing"] == template["Sharing"], "övriga inställningar ska behållas"
    assert cfg["Backend"] == "QEMU" and cfg["ConfigurationVersion"] == 4

print("OK: UTM-paketering: namn, disk, minne, CPU, ny MAC, övrigt orört")

with tempfile.TemporaryDirectory() as temp_dir:
    directory = Path(temp_dir)
    disk = directory / "DegsellOS.qcow2"
    disk.write_bytes(b"QFI\xfb")
    out = directory / "DegsellOS.utm.zip"
    subprocess.run([sys.executable, str(ROOT / "scripts/paketera_utm.py"), str(ROOT / "vm/utm/config.plist"),
                    str(disk), str(out), "--minne", "4096"], check=True, capture_output=True)
    with zipfile.ZipFile(out) as archive:
        cfg = plistlib.loads(archive.read("DegsellOS.utm/config.plist"))
        assert cfg["System"]["MemorySize"] == 4096 and cfg["QEMU"]["UEFIBoot"]
        assert cfg["Display"] and cfg["Network"][0]["Mode"] == "Shared"
        assert cfg["Sharing"]["DirectoryShareMode"] == "VirtFS"
        assert archive.read("DegsellOS.utm/Data/DegsellOS.qcow2") == disk.read_bytes()
        assert archive.read("DegsellOS.utm/LICENSE-mall") == (ROOT / "vm/utm/config.LICENSE").read_bytes()
