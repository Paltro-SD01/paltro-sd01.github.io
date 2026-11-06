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
REPOS_CONFIG = [
    {
        'id': 'LAB-IQ-150',
        'name': 'LAB-IQ-150',
        'category': 'Tribology / Reciprocating Rig',
        'description': 'High-frequency reciprocating multi-axis test rig control software (Heave, Sway, Surge, Traction, Load Cell FGV).',
        'local_path': r'D:\Projects\Software Repo\LAB-IQ 150',
        'github_url': 'https://github.com/Paltro-SD01/LAB-IQ-150',
        'work_order_folders': ['WO 2476']
    },
    {
        'id': 'BOCLE',
        'name': 'BOCLE',
        'category': 'Lubricity Evaluation Rig',
        'description': 'Ball-on-Cylinder Lubricity Evaluator Testing Rig automation, real-time DAQ, calibration, and test reporting.',
        'local_path': r'D:\Projects\Software Repo\BOCLE',
        'github_url': 'https://github.com/Paltro-SD01/BOCLE',
        'work_order_folders': ['WO 2411', 'WO 2414', 'WO 2418 & 2419', 'WO 2427', 'WO 2427  internal', 'WO 2442', 'WO 2443', 'WO 2446 Discontinued', 'WO 2446 Replacement Machine', 'WO 2451', 'WO 2452', 'WO 2453', 'WO 2462', 'WO 2467', 'WO 2479', 'WO 2482', 'WO 2485']
    },
    {
        'id': 'HFRR-ADV',
        'name': 'HFRR-ADV',
        'category': 'High-Precision Wear Rig',
        'description': 'High Frequency Reciprocating Rig Advanced control suite, stroke point calibration and multi-stage testing.',
        'local_path': r'D:\Projects\Software Repo\LAB-IQ\HFRR Adv',
        'github_url': 'https://github.com/Paltro-SD01/HFRR-ADV',
        'work_order_folders': ['WO 2465', 'WO 2472', 'WO 2480']
    },
    {
        'id': 'LAB-IQ-350',
        'name': 'LAB-IQ-350',
        'category': 'Multi-Parameter Tribometer',
        'description': 'Industrial mechanical test platform with RS-485 load cell communication and automated PDF reporting.',
        'local_path': r'D:\Projects\Software Repo\LAB-IQ 350',
        'github_url': 'https://github.com/Paltro-SD01/LAB-IQ-350',
        'work_order_folders': ['WO 2203', 'WO 2394']
    },
    {
        'id': 'B2V2',
        'name': 'B2V2',
        'category': 'Automation & Motion Control',
        'description': 'Multi-axis high-speed synchronized motion controller with real-time tracking loops.',
        'local_path': r'D:\Projects\Software Repo\LAB-IQ\B2V2',
        'github_url': 'https://github.com/Paltro-SD01/B2V2',
        'work_order_folders': ['WO 2470']
    },
    {
        'id': 'AIRJET',
        'name': 'AIRJET',
        'category': 'Erosion Testing Rig',
        'description': 'Solid particle air-jet erosion tester with particle velocity monitoring and erosion resistance quantification.',
        'local_path': r'D:\Projects\Software Repo\LAB-IQ\Airjet',
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

    # Output JS
    js_content = (
        "var DATA_SYNC_META = " + json.dumps(sync_meta, ensure_ascii=False) + ";\n"
        "var REPOS_DATA = " + json.dumps(repos_data, ensure_ascii=False) + ";\n"
    )
    data_js_path = os.path.join(DASHBOARD_DIR, 'data.js')
    with open(data_js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    # Also update device_access_log.json and DEVICE_ACCESS_LOG.md for GitHub cross-verification
    log_json_path = os.path.join(DASHBOARD_DIR, 'device_access_log.json')
    try:
        with open(log_json_path, 'r', encoding='utf-8') as lf:
            access_log = json.load(lf)
            if not isinstance(access_log, list):
                access_log = []
    except Exception:
        access_log = []

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
    if not access_log or access_log[0].get("sync_id") != sync_id or access_log[0].get("device_id") != ws_entry["device_id"]:
        access_log.insert(0, ws_entry)
        access_log = access_log[:200]
        with open(log_json_path, 'w', encoding='utf-8') as lf:
            json.dump(access_log, lf, indent=2, ensure_ascii=False)

    md_lines = [
        "# 🔐 Paltro-SD01 — Device Access & Sync Cross-Verification Log",
        "",
        f"> **Latest Master Sync ID:** `{sync_id}`  ",
        f"> **Last Published:** `{now_str}`  ",
        "> **Purpose:** Cross-verifies every Android phone, tablet, browser, and workstation that accesses or syncs with the Paltro-SD01 Engineering Command Center.",
        "",
        "| Timestamp | Device ID | Device / Model | OS / Platform | Mode | Screen Resolution | IP / Network | Sync Version | Event / Status |",
        "| :--- | :---: | :--- | :--- | :---: | :---: | :--- | :---: | :--- |",
    ]
    for e in access_log:
        md_lines.append(
            f"| `{e.get('timestamp','-')}` | `{e.get('device_id','-')}` | **{e.get('device_name','-')}** | {e.get('platform','-')} | `{e.get('app_mode','-')}` | `{e.get('resolution','-')}` | {e.get('network','-')} | `{e.get('sync_id','-')}` | {e.get('event','Access Verified')} |"
        )
    with open(os.path.join(DASHBOARD_DIR, 'DEVICE_ACCESS_LOG.md'), 'w', encoding='utf-8') as mf:
        mf.write("\n".join(md_lines) + "\n")

    print(f"Successfully generated {data_js_path} ({os.path.getsize(data_js_path)} bytes) [Sync ID: {sync_id}]")

if __name__ == '__main__':
    refresh_data()
