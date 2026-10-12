import os
import sys
import json
import subprocess
from datetime import datetime

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
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 4:
                rows.append(parts)
        elif in_table and not line.startswith('|') and line.strip() != '':
            in_table = False
    return rows

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
        
        raw_log = subprocess.check_output(['git', '-C', p, 'log', '--format=@@@%H|%h|%an|%ae|%ad|%s', '--date=iso', '--name-status']).decode('utf-8', errors='ignore')
        raw_commits = raw_log.split('@@@')[1:]
        commits = []
        
        for rc in raw_commits:
            lines = rc.strip().splitlines()
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
                'files_count': len(files),
                'files': files[:15]
            })
        
        # Parse changelog
        root_cl_path = os.path.join(p, 'CHANGELOG.md')
        root_table = parse_changelog_table(root_cl_path)
        root_table_map = {}
        for r in root_table:
            wo_clean = r[0].replace('*', '').strip()
            status_clean = r[1].replace('`', '').strip() if len(r) > 1 else ''
            hash_clean = r[2].replace('`', '').strip() if len(r) > 2 else ''
            dt_clean = r[3] if len(r) > 3 else ''
            sum_clean = r[4] if len(r) > 4 else ''
            root_table_map[wo_clean] = {
                'status': status_clean,
                'last_commit_hash': hash_clean,
                'last_commit_date': dt_clean,
                'summary': sum_clean
            }
        
        wo_data = []
        for wo_folder in cfg['work_order_folders']:
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
            elif 'TESTING' in status:
                status = 'TESTING'
            elif 'DISCONTINUED' in wo_folder.upper():
                status = 'DISCONTINUED'
                
            wo_data.append({
                'name': wo_folder,
                'path': wo_path,
                'relative_path': wo_folder,
                'status': status,
                'file_count': item_count,
                'last_commit_hash': root_info.get('last_commit_hash', ''),
                'last_commit_date': root_info.get('last_commit_date', ''),
                'summary': root_info.get('summary', ''),
                'has_detailed_changelog': os.path.exists(wo_cl_path)
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
        print(f"Processed {cfg['name']}: {len(commits)} commits, {len(wo_data)} work orders")

    # Output JS and JSON
    js_content = "const REPOS_DATA = " + json.dumps(repos_data, ensure_ascii=False) + ";"
    data_js_path = os.path.join(DASHBOARD_DIR, 'data.js')
    with open(data_js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"Successfully generated {data_js_path} ({os.path.getsize(data_js_path)} bytes)")

if __name__ == '__main__':
    refresh_data()
