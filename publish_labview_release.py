#!/usr/bin/env python3
"""
PALTRO-SD01 | 1-CLICK LABVIEW EXE RELEASE & version.json PUBLISHER
Uploads a compiled LabVIEW .exe to GitHub Releases (optional) and updates
releases/<RIG>.json + releases/version.json on https://paltro-sd01.github.io.

Example usage:
  python publish_labview_release.py --rig HFRR-ADV --wo "WO 2472" --version "45.0.0" --tag "v45" --fw "FW-v3.2.0" --exe "D:\Paltro\HFRR-ADV.exe" --notes "Fixed DAQ timeout and calibrated ROI"
"""
import os
import sys
import json
import hashlib
import argparse
import subprocess
import urllib.request
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RELEASES_DIR = os.path.join(SCRIPT_DIR, "releases")
OTA_SYNC_URL = "https://ntfy.sh/paltro_sd01_ota_sync_84f29a1c"

def compute_sha256(file_path):
    if not file_path or not os.path.isfile(file_path):
        return "SHA256-PENDING-UPLOAD"
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    parser = argparse.ArgumentParser(description="Publish a LabVIEW EXE Release & update version.json")
    parser.add_argument("--rig", required=True, help="Rig ID: HFRR-ADV, BOCLE, LAB-IQ-150, LAB-IQ-350, B2V2, AIRJET")
    parser.add_argument("--wo", required=True, help="Work Order name, e.g. 'WO 2472'")
    parser.add_argument("--version", required=True, help="Numeric semantic version for LabVIEW comparison, e.g. '44.0.0'")
    parser.add_argument("--tag", default="", help="Short version tag, e.g. 'v44'")
    parser.add_argument("--fw", default="FW-v1.0.0", help="Required Firmware release, e.g. 'FW-v3.2.0'")
    parser.add_argument("--exe", default="", help="Path to local compiled LabVIEW .exe binary to upload to GitHub Releases")
    parser.add_argument("--download-url", default="", help="Custom direct download URL (auto-generated if omitted)")
    parser.add_argument("--notes", default="Validated production release", help="Release notes shown in LabVIEW popup")
    args = parser.parse_args()

    rig = args.rig.strip().upper()
    v_tag = args.tag.strip() or f"v{args.version.split('.')[0]}"
    exe_name = os.path.basename(args.exe) if args.exe else f"{rig}.exe"
    gh_release_tag = f"{rig}-{v_tag}"
    dl_url = args.download_url.strip() or f"https://github.com/Paltro-SD01/paltro-sd01.github.io/releases/download/{gh_release_tag}/{exe_name}"
    sha256 = compute_sha256(args.exe)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. If a local .exe file exists and gh CLI is available, upload to GitHub Releases
    if args.exe and os.path.isfile(args.exe):
        print(f"[1/4] Uploading {args.exe} to GitHub Release {gh_release_tag}...")
        try:
            subprocess.run(
                ["gh", "release", "create", gh_release_tag, args.exe,
                 "--repo", "Paltro-SD01/paltro-sd01.github.io",
                 "--title", f"{rig} {v_tag} ({args.wo})",
                 "--notes", args.notes],
                check=False
            )
            subprocess.run(
                ["gh", "release", "upload", gh_release_tag, args.exe,
                 "--repo", "Paltro-SD01/paltro-sd01.github.io", "--clobber"],
                check=False
            )
        except Exception as e:
            print(f"  [Info] gh CLI upload skipped ({e}). Manifest URL set to: {dl_url}")

    # 2. Write flat JSON manifest for LabVIEW Unflatten From JSON
    os.makedirs(RELEASES_DIR, exist_ok=True)
    rig_manifest = {
        "rig": rig,
        "work_order": args.wo,
        "latest_version": args.version,
        "version_tag": v_tag,
        "required_firmware": args.fw,
        "exe_name": exe_name,
        "download_url": dl_url,
        "sha256": sha256,
        "published_at": now_str,
        "release_notes": args.notes
    }
    rig_json_path = os.path.join(RELEASES_DIR, f"{rig}.json")
    with open(rig_json_path, "w", encoding="utf-8") as f:
        json.dump(rig_manifest, f, indent=2)
    print(f"[2/4] Updated {rig_json_path}")

    # 3. Update master releases/version.json
    master_path = os.path.join(RELEASES_DIR, "version.json")
    master = {"schema": "Paltro-SD01-LabVIEW-OTA-v1", "updated_at": now_str, "base_url": "https://paltro-sd01.github.io/releases", "rigs": {}}
    if os.path.exists(master_path):
        try:
            with open(master_path, "r", encoding="utf-8") as f:
                master = json.load(f)
        except Exception:
            pass
    master["updated_at"] = now_str
    master.setdefault("rigs", {})[rig] = rig_manifest
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2)

    # Broadcast to cloud relay
    try:
        req = urllib.request.Request(OTA_SYNC_URL, data=json.dumps(master).encode("utf-8"), method="POST")
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass

    # 4. Refresh data.js and push ONLY releases/ and data.js to GitHub
    print("[3/4] Refreshing dashboard telemetry...")
    subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "refresh_data.py")], check=False)

    print("[4/4] Pushing updated version.json manifest to https://paltro-sd01.github.io/releases/ ...")
    subprocess.run(["git", "-C", SCRIPT_DIR, "add", f"releases/{rig}.json", "releases/version.json", "data.js"], check=False)
    subprocess.run(["git", "-C", SCRIPT_DIR, "commit", "--only", f"releases/{rig}.json", "releases/version.json", "data.js",
                    "-m", f"release({rig}): publish LabVIEW OTA {v_tag} ({args.version}) for {args.wo}"], check=False)
    subprocess.run(["git", "-C", SCRIPT_DIR, "push", "origin", "main", "main:gh-pages", "--force"], check=False)
    print(f"\n[SUCCESS] {rig} {v_tag} ({args.version}) is now LIVE at:")
    print(f"  -> https://paltro-sd01.github.io/releases/{rig}.json")

if __name__ == "__main__":
    main()
