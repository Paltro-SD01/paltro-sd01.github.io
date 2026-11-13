#!/usr/bin/env python3
"""
PALTRO-SD01 | LABVIEW OTA CHECK + DOWNLOAD + SELF-SWAP HELPER (paltro_updater.py)
Can be called directly from LabVIEW's System Exec.vi OR used standalone:
  Check only (prints JSON status for LabVIEW stdout):
    python paltro_updater.py --rig HFRR-ADV --current-version v43 --check-only
  Download & launch swap_update.bat:
    python paltro_updater.py --rig HFRR-ADV --current-version v43 --exe "D:\Paltro\HFRR-ADV.exe" --apply
"""
import os
import sys
import json
import time
import tempfile
import argparse
import subprocess
import urllib.request

BASE_MANIFEST_URL = "https://paltro-sd01.github.io/releases"

def parse_ver_tuple(v_str):
    s = str(v_str or "").strip().lstrip("vV")
    parts = []
    for p in s.replace("-", ".").split("."):
        if p.isdigit():
            parts.append(int(p))
    return tuple(parts) if parts else (0,)

def main():
    parser = argparse.ArgumentParser(description="Paltro-SD01 LabVIEW OTA Auto-Updater")
    parser.add_argument("--rig", required=True, help="Rig ID (e.g. HFRR-ADV, BOCLE, LAB-IQ-150)")
    parser.add_argument("--current-version", default="0.0.0", help="Currently running EXE version (e.g. v43 or 43.0.0)")
    parser.add_argument("--exe", default="", help="Full path to the installed LabVIEW .exe to overwrite")
    parser.add_argument("--check-only", action="store_true", help="Only check version.json and print JSON result")
    parser.add_argument("--apply", action="store_true", help="Download new EXE and trigger swap_update.bat")
    args = parser.parse_args()

    url = f"{BASE_MANIFEST_URL}/{args.rig.upper()}.json?_t={int(time.time())}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Paltro-LabVIEW-OTA/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            manifest = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(json.dumps({"update_available": False, "offline": True, "error": str(e)}))
        sys.exit(0)

    remote_ver = manifest.get("latest_version") or manifest.get("version_tag") or "0.0.0"
    is_newer = parse_ver_tuple(remote_ver) > parse_ver_tuple(args.current_version)
    result = {
        "update_available": is_newer,
        "current_version": args.current_version,
        "latest_version": manifest.get("latest_version", ""),
        "version_tag": manifest.get("version_tag", ""),
        "required_firmware": manifest.get("required_firmware", ""),
        "download_url": manifest.get("download_url", ""),
        "release_notes": manifest.get("release_notes", ""),
    }

    if args.check_only or not args.apply or not is_newer:
        print(json.dumps(result))
        sys.exit(0)

    if not args.exe:
        print(json.dumps({"error": "Missing --exe path for --apply"}))
        sys.exit(1)

    temp_dir = tempfile.gettempdir()
    exe_basename = os.path.basename(args.exe)
    temp_new_exe = os.path.join(temp_dir, f"New_{exe_basename}")
    dl_url = manifest["download_url"]

    print(f"Downloading {dl_url} -> {temp_new_exe}...")
    urllib.request.urlretrieve(dl_url, temp_new_exe)

    bat_path = os.path.join(os.path.dirname(os.path.abspath(args.exe)), "swap_update.bat")
    if not os.path.exists(bat_path):
        bat_path = os.path.join(temp_dir, "swap_update.bat")
        with open(bat_path, "w", encoding="utf-8", newline="\r\n") as bf:
            bf.write("""@echo off
timeout /t 2 /nobreak >NUL
copy /Y "%~2" "%~dpn2_backup.exe" >NUL
move /Y "%~1" "%~2" >NUL
start "" "%~2"
""")

    subprocess.Popen(["cmd.exe", "/c", "start", "", bat_path, temp_new_exe, os.path.abspath(args.exe), manifest.get("version_tag", "")],
                     close_fds=True)
    print(json.dumps({"status": "SWAP_STARTED", "target_exe": args.exe}))

if __name__ == "__main__":
    main()
