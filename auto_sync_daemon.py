import os
import sys
import time
import subprocess
from datetime import datetime

DASHBOARD_DIR = r"D:\Projects\paltro-sd01.github.io"
sys.path.insert(0, DASHBOARD_DIR)

import refresh_data


def get_repos_quick_state():
    """Returns a fast state fingerprint of all 6 local LabVIEW repositories (HEAD commit + WO/version folders)."""
    parts = []
    for cfg in refresh_data.REPOS_CONFIG:
        p = cfg["local_path"]
        if not os.path.exists(p):
            continue
        try:
            head = subprocess.check_output(
                ["git", "-C", p, "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="ignore").strip()
        except Exception:
            head = "none"
        wos = refresh_data.list_wo_folders(p, cfg.get("work_orders", []))
        wo_vers = []
        for w in wos:
            wp = os.path.join(p, w)
            if os.path.isdir(wp):
                try:
                    subs = sorted(
                        d for d in os.listdir(wp)
                        if os.path.isdir(os.path.join(wp, d)) and d.lower().startswith("v")
                    )
                except Exception:
                    subs = []
                wo_vers.append(f"{w}:{','.join(subs)}")
        parts.append(f"{cfg['id']}@{head}[{';'.join(wo_vers)}]")
    return "|".join(parts)


def push_dashboard_changes(reason):
    """Commits and pushes any updated telemetry, team ecosystem, or device access logs in paltro-sd01.github.io."""
    tracked_files = [
        "data.js",
        "device_access_log.json",
        "DEVICE_ACCESS_LOG.md",
        "team_ecosystem.json",
        "TEAM_ECOSYSTEM_AND_RELEASES.md",
    ]
    try:
        st = subprocess.check_output(
            ["git", "-C", DASHBOARD_DIR, "status", "--porcelain"] + tracked_files,
            stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="ignore").strip()
        if not st:
            return False
        subprocess.run(
            ["git", "-C", DASHBOARD_DIR, "add"] + tracked_files,
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        subprocess.run(
            ["git", "-C", DASHBOARD_DIR, "commit", "-m", f"chore(auto-sync): {reason} [skip ci]"],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        subprocess.run(
            ["git", "-C", DASHBOARD_DIR, "push", "origin", "main", "main:gh-pages", "--force"],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pushed to GitHub: {reason}", flush=True)
        return True
    except Exception as e:
        print(f"[Warn] Push error: {e}", flush=True)
        return False


def run_daemon():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Paltro-SD01 Auto-Sync & Device Access Logger Daemon started.", flush=True)
    last_repo_state = get_repos_quick_state()

    while True:
        try:
            # 1. Check if any local LabVIEW repository had a commit or Work Order folder update
            curr_state = get_repos_quick_state()
            if curr_state != last_repo_state:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Detected repository change! Rebuilding changelogs, READMEs & data.js...", flush=True)
                subprocess.run([sys.executable, r"D:\Projects\update_all_configs.py"], check=False)
                refresh_data.refresh_data()
                push_dashboard_changes("auto-sync repository updates & work orders")
                last_repo_state = get_repos_quick_state()

            # 2. Check if Team Roster / Firmware / Release Links were edited on Dashboard/Android
            _, eco_changed = refresh_data.sync_team_ecosystem()
            if eco_changed:
                refresh_data.refresh_data()
                push_dashboard_changes("auto-sync team roster & cross-department release links")

            # 3. Pull any new mobile/web device access check-ins and auto-commit to GitHub DEVICE_ACCESS_LOG.md
            logs_changed = refresh_data.sync_device_logs()
            if logs_changed:
                push_dashboard_changes("auto-log device access telemetry to DEVICE_ACCESS_LOG.md")

        except Exception as err:
            print(f"[Daemon Error] {err}", flush=True)

        time.sleep(12)


if __name__ == "__main__":
    run_daemon()
