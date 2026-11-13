import os
import re
import sys
import json
import subprocess
from datetime import datetime

# Force UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))

def resolve_repo_root():
    """Finds the local Software Department repository root on ANY team PC or CI runner."""
    env_root = os.environ.get("PALTRO_REPO_ROOT")
    if env_root and os.path.isdir(env_root):
        return env_root
    local_cfg = os.path.join(DASHBOARD_DIR, "team_local_config.json")
    if os.path.exists(local_cfg):
        try:
            with open(local_cfg, "r", encoding="utf-8") as cf:
                c = json.load(cf)
                if c.get("repo_root") and os.path.isdir(c["repo_root"]):
                    return c["repo_root"]
        except Exception:
            pass
    for candidate in [
        os.path.join(os.path.dirname(DASHBOARD_DIR), "Software Repo"),
        r"D:\Projects\Software Repo",
        r"C:\Projects\Software Repo",
        os.path.dirname(DASHBOARD_DIR),
    ]:
        if os.path.isdir(candidate):
            return candidate
    return r"D:\Projects\Software Repo"

REPO_ROOT = resolve_repo_root()

def resolve_single_repo(rel_candidates):
    for rel in rel_candidates:
        p = os.path.join(REPO_ROOT, rel)
        if os.path.isdir(p):
            return p
    return os.path.join(REPO_ROOT, rel_candidates[0])

REPOS_CONFIG = [
    {
        'id': 'LAB-IQ-150',
        'name': 'LAB-IQ-150',
        'department': 'SOFTWARE',
        'category': 'Tribology / Reciprocating Rig',
        'description': 'High-frequency reciprocating multi-axis test rig control software (Heave, Sway, Surge, Traction, Load Cell FGV).',
        'local_path': resolve_single_repo(['LAB-IQ 150', 'LAB-IQ-150']),
        'github_url': 'https://github.com/Paltro-SD01/LAB-IQ-150',
        'work_order_folders': ['WO 2476', 'WO 2487']
    },
    {
        'id': 'BOCLE',
        'name': 'BOCLE',
        'department': 'SOFTWARE',
        'category': 'Lubricity Evaluation Rig',
        'description': 'Ball-on-Cylinder Lubricity Evaluator Testing Rig automation, real-time DAQ, calibration, and test reporting.',
        'local_path': resolve_single_repo(['BOCLE']),
        'github_url': 'https://github.com/Paltro-SD01/BOCLE',
        'work_order_folders': ['WO 2411', 'WO 2414', 'WO 2418 & 2419', 'WO 2427', 'WO 2427  internal', 'WO 2442', 'WO 2443', 'WO 2446 Discontinued', 'WO 2446 Replacement Machine', 'WO 2451', 'WO 2452', 'WO 2453', 'WO 2462', 'WO 2467', 'WO 2479', 'WO 2482', 'WO 2485']
    },
    {
        'id': 'HFRR-ADV',
        'name': 'HFRR-ADV',
        'department': 'SOFTWARE',
        'category': 'High-Precision Wear Rig',
        'description': 'High Frequency Reciprocating Rig Advanced control suite, stroke point calibration and multi-stage testing.',
        'local_path': resolve_single_repo([os.path.join('LAB-IQ', 'HFRR Adv'), 'HFRR-ADV', 'HFRR Adv']),
        'github_url': 'https://github.com/Paltro-SD01/HFRR-ADV',
        'work_order_folders': ['WO 2465', 'WO 2472', 'WO 2480', 'WO 2486']
    },
    {
        'id': 'LAB-IQ-350',
        'name': 'LAB-IQ-350',
        'department': 'SOFTWARE',
        'category': 'Multi-Parameter Tribometer',
        'description': 'Industrial mechanical test platform with RS-485 load cell communication and automated PDF reporting.',
        'local_path': resolve_single_repo(['LAB-IQ 350', 'LAB-IQ-350']),
        'github_url': 'https://github.com/Paltro-SD01/LAB-IQ-350',
        'work_order_folders': ['WO 2203', 'WO 2394', 'WO 2494']
    },
    {
        'id': 'B2V2',
        'name': 'B2V2',
        'department': 'SOFTWARE',
        'category': 'Automation & Motion Control',
        'description': 'Multi-axis high-speed synchronized motion controller with real-time tracking loops.',
        'local_path': resolve_single_repo([os.path.join('LAB-IQ', 'B2V2'), 'B2V2']),
        'github_url': 'https://github.com/Paltro-SD01/B2V2',
        'work_order_folders': ['WO 2470']
    },
    {
        'id': 'AIRJET',
        'name': 'AIRJET',
        'department': 'SOFTWARE',
        'category': 'Erosion Testing Rig',
        'description': 'Solid particle air-jet erosion tester with particle velocity monitoring and erosion resistance quantification.',
        'local_path': resolve_single_repo([os.path.join('LAB-IQ', 'Airjet'), 'AIRJET', 'Airjet']),
        'github_url': 'https://github.com/Paltro-SD01/AIRJET',
        'work_order_folders': ['Erosion Tester']
    }
]

def list_wo_folders(repo_path, fallback=None):
    """Auto-discovers Work Order folders that physically exist in the repository
    (same rule as update_all_configs.py), so new WOs show up without editing this file."""
    found = []
    try:
        for entry in os.listdir(repo_path):
            up = entry.upper()
            if os.path.isdir(os.path.join(repo_path, entry)) and ('WO' in up or 'WORKORDER' in up or 'EROSION' in up):
                found.append(entry)
    except OSError:
        pass
    found.sort()
    return found or list(fallback or [])


_PIPE_SPLIT = re.compile(r'(?<!\\)\|')


def split_md_row(line):
    """Splits a markdown table row on unescaped pipes."""
    cells = _PIPE_SPLIT.split(line.strip())[1:-1]
    return [c.strip().replace('\\|', '|') for c in cells]


def split_summary(cell):
    """'**Subject**<br>• line2<br>• line3' -> ('Subject', ['line2', 'line3'])."""
    parts = [p.strip() for p in cell.split('<br>')]
    subject = parts[0].replace('**', '').strip() if parts else ''
    details = [p.lstrip('•').strip() for p in parts[1:] if p.strip()]
    return subject, details


def parse_changelog_table(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    rows = []
    lines = content.splitlines()
    in_table = False
    for line in lines:
        if '| Work Order' in line or '| Date & Time' in line:
            in_table = True
            continue
        if in_table and line.startswith('|') and not line.startswith('| :---'):
            parts = split_md_row(line)
            if len(parts) >= 4:
                rows.append(parts)
        elif in_table and not line.startswith('|') and line.strip() != '':
            in_table = False
    return rows

def parse_wo_detailed_changelog(file_path):
    """Parses individual Work Order CHANGELOG.md file into structured entries grouped by category."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    entries = []
    current_section = 'General'
    
    for line in content.splitlines():
        line_s = line.strip()
        if line_s.startswith('### '):
            current_section = line_s.replace('### ', '').strip()
            continue
        if line_s.startswith('|') and not line_s.startswith('| :---') and not line_s.startswith('| Date'):
            parts = split_md_row(line_s)
            if len(parts) >= 4:
                clean_commit = parts[1].replace('`', '').strip()
                subject, details = split_summary(parts[2])
                entries.append({
                    'category': current_section,
                    'date': parts[0].strip(),
                    'commit_hash': clean_commit,
                    'summary': subject,
                    'details': details,
                    'author': parts[3].replace('`', '').strip()
                })
    return entries

def refresh_data():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Refreshing repository data...")
    repos_data = []

    for cfg in REPOS_CONFIG:
        p = cfg['local_path']
        if not os.path.exists(p):
            print(f"Skipping {cfg['name']} (Path not found: {p})")
            continue
        
        branch = subprocess.check_output(['git', '-C', p, 'branch', '--show-current']).decode('utf-8', errors='ignore').strip()
        total_commits = int(subprocess.check_output(['git', '-C', p, 'rev-list', '--count', 'HEAD']).decode().strip())
        
        remotes = subprocess.check_output(['git', '-C', p, 'remote', '-v']).decode('utf-8', errors='ignore').splitlines()
        push_remote = remotes[1].split()[1] if len(remotes) > 1 else (remotes[0].split()[1] if remotes else cfg['github_url'])
        
        tags = subprocess.check_output(['git', '-C', p, 'tag', '-l', '--sort=-v:refname']).decode('utf-8', errors='ignore').split()
        
        raw_log = subprocess.check_output(['git', '-C', p, 'log', '--format=@@@%H|%h|%an|%ae|%ad|%s%x1e%b%x1e', '--date=iso', '--name-status']).decode('utf-8', errors='ignore')
        raw_commits = raw_log.split('@@@')[1:]
        commits = []
        
        for rc in raw_commits:
            segs = rc.split('\x1e')
            body_txt = segs[1].strip() if len(segs) > 2 else ''
            lines = (segs[0] + ('\n' + segs[2] if len(segs) > 2 else '')).strip().splitlines()
            if not lines: continue
            hdr = lines[0].split('|', 5)
            if len(hdr) < 6: continue
            
            full_h, short_h, author, email, dt, subj = hdr
            files = []
            for fl in lines[1:]:
                fl = fl.strip()
                if not fl: continue
                fl_p = fl.split('\t')
                if len(fl_p) >= 2:
                    files.append({'status': fl_p[0], 'path': fl_p[1]})
            
            commits.append({
                'hash': full_h,
                'short_hash': short_h,
                'author': author,
                'email': email,
                'date': dt,
                'subject': subj,
                'body': [l.strip() for l in body_txt.splitlines() if l.strip()][:12],
                'files_count': len(files),
                'files': files[:15]
            })
        
        # 1. Parse Root Master CHANGELOG.md (Latest commit per Work Order)
        root_cl_path = os.path.join(p, 'CHANGELOG.md')
        root_table = parse_changelog_table(root_cl_path)
        root_table_map = {}
        for r in root_table:
            wo_clean = r[0].replace('*', '').strip()
            # Master CHANGELOG.md columns:
            # [0] Work Order, [1] LabVIEW Version, [2] Status, [3] Hash, [4] Date, [5] Summary, [6] Author
            ver_clean = r[1].replace('`', '').strip() if len(r) > 1 else 'v01'
            status_clean = r[2].replace('`', '').strip() if len(r) > 2 else ''
            hash_clean = r[3].replace('`', '').strip() if len(r) > 3 else ''
            dt_clean = r[4] if len(r) > 4 else ''
            sum_clean, sum_details = split_summary(r[5]) if len(r) > 5 else ('', [])
            root_table_map[wo_clean] = {
                'version': ver_clean,
                'status': status_clean,
                'last_commit_hash': hash_clean,
                'last_commit_date': dt_clean,
                'summary': sum_clean,
                'details': sum_details
            }
        
        # 2. Parse Sub-Changelog inside every Work Order folder (Full history of that particular Work Order)
        wo_data = []
        for wo_folder in list_wo_folders(p, cfg.get('work_order_folders')):
            wo_path = os.path.join(p, wo_folder)
            wo_cl_path = os.path.join(wo_path, 'CHANGELOG.md')
            
            item_count = 0
            if os.path.exists(wo_path):
                item_count = sum([len(files) for r, d, files in os.walk(wo_path) if '.git' not in r])
            
            root_info = root_table_map.get(wo_folder, {})
            status = root_info.get('status', 'ACTIVE')
            if not status: status = 'ACTIVE'
            if 'CLOSED' in status or '🔒' in status:
                status = 'CLOSED'
            elif 'TESTING' in status or 'INTEGRATION' in status:
                status = 'TESTING'
            elif 'REOPENED' in status:
                status = 'ACTIVE'
            elif 'DISCONTINUED' in wo_folder.upper():
                status = 'DISCONTINUED'
            
            # Read all historical commits belonging to this specific work order
            detailed_history = parse_wo_detailed_changelog(wo_cl_path)
                
            wo_data.append({
                'name': wo_folder,
                'path': wo_path,
                'relative_path': wo_folder,
                'status': status,
                'version': root_info.get('version', 'v01'),
                'file_count': item_count,
                'last_commit_hash': root_info.get('last_commit_hash', ''),
                'last_commit_date': root_info.get('last_commit_date', ''),
                'summary': root_info.get('summary', ''),
                'details': root_info.get('details', []),
                'has_detailed_changelog': os.path.exists(wo_cl_path),
                'detailed_history_count': len(detailed_history),
                'detailed_history': detailed_history
            })
        
        repos_data.append({
            'id': cfg['id'],
            'name': cfg['name'],
            'category': cfg['category'],
            'description': cfg['description'],
            'local_path': p,
            'push_remote': push_remote,
            'github_url': cfg['github_url'],
            'branch': branch,
            'total_commits': total_commits,
            'tags_count': len(tags),
            'latest_tag': tags[0] if tags else 'None',
            'tags': tags,
            'latest_commit': commits[0] if commits else None,
            'work_orders': wo_data,
            'commits': commits
        })
        print(f"Processed {cfg['name']}: {len(commits)} total commits, {len(wo_data)} work orders parsed with full sub-changelogs.")

    if not repos_data:
        print('No repositories found on this machine - leaving data.js untouched.')
        return

    import hashlib, platform, socket
    digest_src = "|".join(
        f"{r['id']}:{r['total_commits']}:{(r['latest_commit'] or {}).get('short_hash','')}"
        + ":" + ",".join(f"{w['name']}={w['version']}/{w['status']}/{w['last_commit_hash']}" for w in r['work_orders'])
        for r in repos_data
    )
    sync_id = "SYNC-" + hashlib.sha256(digest_src.encode("utf-8")).hexdigest()[:8].upper()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sync_meta = {
        "sync_id": sync_id,
        "generated_at": now_str,
        "host": socket.gethostname(),
        "total_repos": len(repos_data),
        "total_commits": sum(r["total_commits"] for r in repos_data),
        "total_work_orders": sum(len(r["work_orders"]) for r in repos_data),
    }

    # Sync Team Roster, Multi-Department Repos & Software<->Firmware Release Links
    ecosystem_data, _ = sync_team_ecosystem(repos_data=repos_data, now_str=now_str)
    ota_data, _ = sync_ota_releases(repos_data=repos_data, ecosystem_data=ecosystem_data, now_str=now_str)

    # Output JS
    js_content = (
        "var DATA_SYNC_META = " + json.dumps(sync_meta, ensure_ascii=False) + ";\n"
        "var TEAM_ECOSYSTEM_DATA = " + json.dumps(ecosystem_data, ensure_ascii=False) + ";\n"
        "var LABVIEW_OTA_DATA = " + json.dumps(ota_data, ensure_ascii=False) + ";\n"
        "var REPOS_DATA = " + json.dumps(repos_data, ensure_ascii=False) + ";\n"
    )
    data_js_path = os.path.join(DASHBOARD_DIR, 'data.js')
    with open(data_js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    # Also update device_access_log.json and DEVICE_ACCESS_LOG.md for GitHub cross-verification
    sync_device_logs(sync_id=sync_id, now_str=now_str, sync_meta=sync_meta)

    print(f"Successfully generated {data_js_path} ({os.path.getsize(data_js_path)} bytes) [Sync ID: {sync_id}]")


RELAY_TOPIC_URL = "https://ntfy.sh/paltro_sd01_device_log_84f29a1c"
ECOSYSTEM_TOPIC_URL = "https://ntfy.sh/paltro_sd01_ecosystem_sync_84f29a1c"
OTA_TOPIC_URL = "https://ntfy.sh/paltro_sd01_ota_sync_84f29a1c"


def sync_ota_releases(repos_data=None, ecosystem_data=None, now_str=None):
    """Syncs /releases/<RIG>.json and /releases/version.json with cloud edits and latest WO versions."""
    import urllib.request
    releases_dir = os.path.join(DASHBOARD_DIR, "releases")
    os.makedirs(releases_dir, exist_ok=True)
    master_path = os.path.join(releases_dir, "version.json")
    try:
        with open(master_path, "r", encoding="utf-8") as mf:
            master = json.load(mf)
    except Exception:
        master = {"schema": "Paltro-SD01-LabVIEW-OTA-v1", "updated_at": now_str or "", "base_url": "https://paltro-sd01.github.io/releases", "rigs": {}}

    orig_dump = json.dumps(master, sort_keys=True)

    # Pull any live OTA manifest edits broadcast from the Dashboard UI
    try:
        req = urllib.request.Request(
            f"{OTA_TOPIC_URL}/json?poll=1&since=48h",
            headers={"User-Agent": "Paltro-SD01-OTA-Sync/1.0"}
        )
        newest_cloud = None
        newest_ts = str(master.get("updated_at", ""))
        with urllib.request.urlopen(req, timeout=6) as resp:
            for raw_line in resp.read().decode("utf-8", errors="ignore").splitlines():
                if not raw_line.strip():
                    continue
                try:
                    outer = json.loads(raw_line)
                    if outer.get("event") == "message" and outer.get("message"):
                        p = json.loads(outer["message"])
                        if isinstance(p, dict) and "rigs" in p:
                            ts = str(p.get("updated_at", ""))
                            if ts >= newest_ts:
                                newest_ts = ts
                                newest_cloud = p
                except Exception:
                    pass
        if newest_cloud:
            master = newest_cloud
    except Exception:
        pass

    rigs_dict = master.setdefault("rigs", {})
    for rig_id, r_manifest in rigs_dict.items():
        rig_file = os.path.join(releases_dir, f"{rig_id}.json")
        if not os.path.exists(rig_file) or json.dumps(master, sort_keys=True) != orig_dump:
            with open(rig_file, "w", encoding="utf-8") as rf:
                json.dump(r_manifest, rf, indent=2, ensure_ascii=False)

    changed = json.dumps(master, sort_keys=True) != orig_dump
    if changed or not os.path.exists(master_path):
        with open(master_path, "w", encoding="utf-8") as mf:
            json.dump(master, mf, indent=2, ensure_ascii=False)

    return master, changed


def sync_team_ecosystem(repos_data=None, now_str=None):
    """Syncs team_ecosystem.json with any live edits broadcast from Dashboard/Android UI,
    auto-detects [FW:...] tags from commits, and writes TEAM_ECOSYSTEM_AND_RELEASES.md."""
    import urllib.request
    eco_path = os.path.join(DASHBOARD_DIR, "team_ecosystem.json")
    try:
        with open(eco_path, "r", encoding="utf-8") as ef:
            eco = json.load(ef)
    except Exception:
        eco = {"departments": [], "team_roster": [], "firmware_releases": [], "release_links": []}

    original_dump = json.dumps(eco, sort_keys=True)

    # Check if a newer ecosystem payload was saved via Web Dashboard / Android App
    try:
        req = urllib.request.Request(
            f"{ECOSYSTEM_TOPIC_URL}/json?poll=1&since=48h",
            headers={"User-Agent": "Paltro-SD01-Ecosystem-Sync/1.0"}
        )
        latest_cloud = None
        latest_ts = str(eco.get("updated_at", ""))
        with urllib.request.urlopen(req, timeout=8) as resp:
            for raw_line in resp.read().decode("utf-8", errors="ignore").splitlines():
                if not raw_line.strip():
                    continue
                try:
                    outer = json.loads(raw_line)
                    if outer.get("event") == "message" and outer.get("message"):
                        p = json.loads(outer["message"])
                        if isinstance(p, dict) and "team_roster" in p and "release_links" in p:
                            ts = str(p.get("updated_at", ""))
                            if ts >= latest_ts:
                                latest_ts = ts
                                latest_cloud = p
                except Exception:
                    pass
        if latest_cloud:
            eco = latest_cloud
    except Exception:
        pass

    # Auto-detect [FW:...] tags from Software Work Order commits and keep sw_version in sync
    if repos_data:
        links = eco.setdefault("release_links", [])
        for r in repos_data:
            for w in r.get("work_orders", []):
                # Update sw_version on existing links for this repo + wo
                for lnk in links:
                    if lnk.get("sw_repo") == r["id"] and lnk.get("sw_wo") == w["name"]:
                        if w.get("version"):
                            lnk["sw_version"] = w["version"]
                # Check if summary has [FW:...] tag
                text_blob = (w.get("summary") or "") + " " + " ".join(w.get("details") or [])
                m_fw = re.search(r"\[FW:([^\]]+)\]", text_blob, re.I)
                if m_fw:
                    fw_ver = m_fw.group(1).strip()
                    exists = any(l.get("sw_repo") == r["id"] and l.get("sw_wo") == w["name"] and l.get("fw_version") == fw_ver for l in links)
                    if not exists:
                        links.insert(0, {
                            "link_id": f"REL-AUTO-{len(links)+1:02d}",
                            "rig": r["id"],
                            "sw_repo": r["id"],
                            "sw_wo": w["name"],
                            "sw_version": w.get("version", "v01"),
                            "fw_id": f"FW-{r['id']}",
                            "fw_version": fw_ver,
                            "hw_revision": "PCB-Std",
                            "compatibility": "VERIFIED" if w.get("status") == "CLOSED" else "INTEGRATION",
                            "verified_by": "Auto-Linked from Commit",
                            "updated_at": (now_str or datetime.now().strftime('%Y-%m-%d'))[:10],
                            "notes": w.get("summary", "Linked via commit tag")
                        })

    changed = json.dumps(eco, sort_keys=True) != original_dump
    if changed or not os.path.exists(os.path.join(DASHBOARD_DIR, "TEAM_ECOSYSTEM_AND_RELEASES.md")):
        with open(eco_path, "w", encoding="utf-8") as ef:
            json.dump(eco, ef, indent=2, ensure_ascii=False)

        md = [
            "# 🌐 Paltro-SD01 — Multi-PC Team Roster & Cross-Department Release Matrix",
            "",
            f"> **Last Updated:** `{eco.get('updated_at', now_str or '-')}`  ",
            "> **Departments Covered:** Software Dept (`SW`) · Firmware Dept (`FW`) · Electronics/Hardware (`HW`) · Rig QA (`QA`)  ",
            "",
            "## 👨‍💻 Active Engineering Team & Workstation Roster",
            "",
            "| ID | Engineer Name | Role | Department | Workstation PC | Local Repo Root | Active Repo / WO | Status |",
            "| :---: | :--- | :--- | :---: | :---: | :--- | :---: | :---: |",
        ]
        for m in eco.get("team_roster", []):
            md.append(
                f"| `{m.get('id','-')}` | **{m.get('name','-')}** | {m.get('role','-')} | `{m.get('department','-')}` | `{m.get('pc_name','-')}` | `{m.get('repo_root','-')}` | `{m.get('active_repo','-')} / {m.get('active_wo','-')}` | `{m.get('status','ONLINE')}` |"
            )

        md.extend([
            "",
            "## 🔗 Cross-Department Linked Release Matrix (Software Release ↔ Firmware Release)",
            "",
            "| Link ID | Rig / Platform | Software Work Order | SW Version | Linked Firmware Repo | Firmware Version | HW / PCB Rev | Compatibility | Verified By | Notes |",
            "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |",
        ])
        for l in eco.get("release_links", []):
            md.append(
                f"| `{l.get('link_id','-')}` | **{l.get('rig','-')}** | `{l.get('sw_wo','-')}` | `{l.get('sw_version','-')}` | `{l.get('fw_id','-')}` | **`{l.get('fw_version','-')}`** | `{l.get('hw_revision','-')}` | `{l.get('compatibility','VERIFIED')}` | {l.get('verified_by','-')} | {l.get('notes','-')} |"
            )

        md.extend([
            "",
            "## 🔌 Firmware Department Releases Registry",
            "",
            "| Firmware ID | Target Rig | MCU / Controller | Firmware Version | Protocol | Checksum | Status | Release Notes |",
            "| :---: | :---: | :--- | :---: | :--- | :---: | :---: | :--- |",
        ])
        for fw in eco.get("firmware_releases", []):
            md.append(
                f"| `{fw.get('id','-')}` | **{fw.get('rig','-')}** | {fw.get('mcu_target','-')} | **`{fw.get('version','-')}`** | `{fw.get('protocol','-')}` | `{fw.get('checksum','-')}` | `{fw.get('status','RELEASED')}` | {fw.get('notes','-')} |"
            )

        with open(os.path.join(DASHBOARD_DIR, "TEAM_ECOSYSTEM_AND_RELEASES.md"), "w", encoding="utf-8") as mf:
            mf.write("\n".join(md) + "\n")

    return eco, changed


def fetch_cloud_relay_logs():
    """Fetches real-time device check-ins posted automatically by Android/Web clients."""
    import urllib.request
    entries = []
    try:
        req = urllib.request.Request(
            f"{RELAY_TOPIC_URL}/json?poll=1&since=48h",
            headers={"User-Agent": "Paltro-SD01-Sync-Engine/1.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            for raw_line in resp.read().decode("utf-8", errors="ignore").splitlines():
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    outer = json.loads(raw_line)
                    if outer.get("event") == "message" and outer.get("message"):
                        payload = json.loads(outer["message"])
                        if isinstance(payload, dict) and payload.get("device_id"):
                            entries.append(payload)
                except Exception:
                    pass
    except Exception:
        pass
    return entries


def sync_device_logs(sync_id=None, now_str=None, sync_meta=None):
    import platform, socket
    log_json_path = os.path.join(DASHBOARD_DIR, 'device_access_log.json')
    try:
        with open(log_json_path, 'r', encoding='utf-8') as lf:
            access_log = json.load(lf)
            if not isinstance(access_log, list):
                access_log = []
    except Exception:
        access_log = []

    if not now_str:
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not sync_id:
        sync_id = access_log[0].get("sync_id", "LIVE") if access_log else "LIVE"

    cloud_entries = fetch_cloud_relay_logs()
    combined = []

    if sync_meta:
        ws_entry = {
            "timestamp": now_str,
            "device_id": f"WS-{socket.gethostname().upper()}",
            "device_name": f"{socket.gethostname()} (Engineering Workstation)",
            "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "app_mode": "Workstation Master Publisher",
            "resolution": "Desktop Master",
            "network": "Local Workstation Git Sync",
            "sync_id": sync_id,
            "event": f"Published {sync_meta['total_work_orders']} WOs / {sync_meta['total_commits']} Commits"
        }
        combined.append(ws_entry)

    # Newest cloud entries first
    for ce in reversed(cloud_entries):
        combined.append(ce)
    for old in access_log:
        combined.append(old)

    # Deduplicate by (device_id, timestamp) or consecutive identical (device_id, sync_id, event)
    deduped = []
    seen_keys = set()
    for item in combined:
        k = f"{item.get('device_id','')}|{item.get('timestamp','')}"
        if k in seen_keys:
            continue
        if deduped:
            prev = deduped[-1]
            if (prev.get("device_id") == item.get("device_id")
                    and prev.get("sync_id") == item.get("sync_id")
                    and prev.get("event") == item.get("event")
                    and str(prev.get("timestamp", ""))[:15] == str(item.get("timestamp", ""))[:15]):
                continue
        seen_keys.add(k)
        deduped.append(item)

    deduped.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    deduped = deduped[:250]

    changed = json.dumps(deduped, sort_keys=True) != json.dumps(access_log, sort_keys=True)
    if changed or not os.path.exists(os.path.join(DASHBOARD_DIR, 'DEVICE_ACCESS_LOG.md')):
        with open(log_json_path, 'w', encoding='utf-8') as lf:
            json.dump(deduped, lf, indent=2, ensure_ascii=False)

        md_lines = [
            "# 🔐 Paltro-SD01 — Automatic Device Access & Sync Cross-Verification Log",
            "",
            f"> **Latest Master Sync ID:** `{sync_id}`  ",
            f"> **Last Updated:** `{now_str}`  ",
            "> **Mode:** `100% Automatic Real-Time Device Telemetry & GitHub Audit Log`  ",
            "> **Purpose:** Automatically logs every Android phone, tablet, browser, and workstation that accesses or syncs with the Paltro-SD01 Engineering Command Center.",
            "",
            "| Timestamp | Device ID | Device / Model | OS / Platform | Mode | Screen Resolution | IP / Network | Sync Version | Event / Status |",
            "| :--- | :---: | :--- | :--- | :---: | :---: | :--- | :---: | :--- |",
        ]
        for e in deduped:
            md_lines.append(
                f"| `{e.get('timestamp','-')}` | `{e.get('device_id','-')}` | **{e.get('device_name','-')}** | {e.get('platform','-')} | `{e.get('app_mode','-')}` | `{e.get('resolution','-')}` | {e.get('network','-')} | `{e.get('sync_id','-')}` | {e.get('event','Auto-Verified')} |"
            )
        with open(os.path.join(DASHBOARD_DIR, 'DEVICE_ACCESS_LOG.md'), 'w', encoding='utf-8') as mf:
            mf.write("\n".join(md_lines) + "\n")
    return changed

if __name__ == '__main__':
    refresh_data()
