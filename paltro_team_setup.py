#!/usr/bin/env python3
"""
PALTRO-SD01 | MULTI-PC TEAM ECOSYSTEM ONBOARDING & AUTO-SYNC SCRIPT (Python Edition)
Run this script on any new Engineering PC (PC 1 .. PC 6) to clone/sync all 6 Software
Department repositories, configure path-independent scripts, and register the PC.
"""
import os
import sys
import json
import shutil
import socket
import getpass
import subprocess
import urllib.request
from datetime import datetime

REPOS = [
    ("LAB-IQ-150", "https://github.com/Paltro-SD01/LAB-IQ-150.git", "LAB-IQ 150"),
    ("BOCLE",      "https://github.com/Paltro-SD01/BOCLE.git",      "BOCLE"),
    ("HFRR-ADV",   "https://github.com/Paltro-SD01/HFRR-ADV.git",   os.path.join("LAB-IQ", "HFRR Adv")),
    ("LAB-IQ-350", "https://github.com/Paltro-SD01/LAB-IQ-350.git", "LAB-IQ 350"),
    ("B2V2",       "https://github.com/Paltro-SD01/B2V2.git",       os.path.join("LAB-IQ", "B2V2")),
    ("AIRJET",     "https://github.com/Paltro-SD01/AIRJET.git",     os.path.join("LAB-IQ", "Airjet")),
]

def main():
    engineer = os.environ.get("PALTRO_ENGINEER", getpass.getuser())
    pc_name = socket.gethostname()
    dept = os.environ.get("PALTRO_DEPT", "SOFTWARE")
    default_root = r"D:\Projects\Software Repo" if os.path.exists("D:\\") else r"C:\Projects\Software Repo"
    workspace_root = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PALTRO_REPO_ROOT", default_root)

    print("=" * 62)
    print("  PALTRO-SD01 | MULTI-PC ENGINEERING ECOSYSTEM SETUP")
    print("=" * 62)
    print(f"  Engineer   : {engineer}")
    print(f"  PC Name    : {pc_name}")
    print(f"  Department : {dept}")
    print(f"  Repo Root  : {workspace_root}")
    print("=" * 62)

    os.makedirs(workspace_root, exist_ok=True)
    os.makedirs(os.path.join(workspace_root, "LAB-IQ"), exist_ok=True)
    parent_dir = os.path.dirname(workspace_root)

    print("\n[1/3] Synchronizing 6 Software Department Repositories...")
    for name, url, subpath in REPOS:
        target = os.path.join(workspace_root, subpath)
        if os.path.isdir(os.path.join(target, ".git")):
            print(f"  -> Pulling latest {name} at {target}...")
            subprocess.run(["git", "-C", target, "pull", "origin", "main", "--rebase", "--autostash"], check=False)
        else:
            print(f"  -> Cloning {name} into {target}...")
            subprocess.run(["git", "clone", url, target], check=False)

    dash_path = os.path.join(parent_dir, "paltro-sd01.github.io")
    print("\n[2/3] Synchronizing Command Center & Automation Scripts...")
    if os.path.isdir(os.path.join(dash_path, ".git")):
        subprocess.run(["git", "-C", dash_path, "pull", "origin", "main", "--rebase", "--autostash"], check=False)
    else:
        subprocess.run(["git", "clone", "https://github.com/Paltro-SD01/paltro-sd01.github.io.git", dash_path], check=False)

    src_cfg = os.path.join(dash_path, "update_all_configs.py")
    if os.path.isfile(src_cfg):
        shutil.copy2(src_cfg, os.path.join(parent_dir, "update_all_configs.py"))

    local_cfg = {
        "engineer_name": engineer,
        "pc_name": pc_name,
        "department": dept,
        "repo_root": workspace_root,
        "dashboard_dir": dash_path,
        "configured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    for cfg_dest in [os.path.join(dash_path, "team_local_config.json"), os.path.join(parent_dir, "team_local_config.json")]:
        try:
            with open(cfg_dest, "w", encoding="utf-8") as f:
                json.dump(local_cfg, f, indent=2)
        except Exception:
            pass

    print(f"\n[3/3] Registering Workstation {pc_name} in Paltro-SD01 Ecosystem...")
    beacon = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device_id": f"PC-{pc_name}",
        "device_name": f"{engineer} ({pc_name})",
        "platform": f"Windows Workstation ({dept} Dept)",
        "app_mode": "Team Workstation Node",
        "resolution": "Workstation CLI",
        "network": workspace_root,
        "sync_id": "TEAM-ONBOARD",
        "event": f"Onboarded Team PC ({dept} Dept)"
    }
    try:
        req = urllib.request.Request(
            "https://ntfy.sh/paltro_sd01_device_log_84f29a1c",
            data=json.dumps(beacon).encode("utf-8"),
            method="POST"
        )
        urllib.request.urlopen(req, timeout=6)
    except Exception:
        pass

    print(f"\n[OK] Setup Complete! {pc_name} is now connected to the Paltro-SD01 Ecosystem.")
    print("     Open https://paltro-sd01.github.io to view the Team Roster & Release Matrix.")

if __name__ == "__main__":
    main()
