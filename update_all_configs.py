import os
import subprocess
import sys
import shutil
import re

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import glob
import json

def find_git_cliff():
    which_bin = shutil.which("git-cliff") or shutil.which("git-cliff.exe")
    if which_bin:
        return which_bin
    local_app = os.environ.get("LOCALAPPDATA", r"C:\Users\Admin\AppData\Local")
    matches = glob.glob(os.path.join(local_app, "Microsoft", "WinGet", "Packages", "*git-cliff*", "**", "git-cliff.exe"), recursive=True)
    if matches:
        return matches[0]
    fallback = r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\orhun.git-cliff_Microsoft.Winget.Source_8wekyb3d8bbwe\git-cliff-2.14.1\git-cliff.exe"
    return fallback if os.path.exists(fallback) else "git-cliff"

GIT_CLIFF_BIN = find_git_cliff()
GIT_BIN = shutil.which("git") or shutil.which("git.exe") or "git.exe"

import argparse

def parse_cli_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--repo", "-r", default=None, help="Target only a single repository path")
    parser.add_argument("--wo", "-w", default=None, help="Target only a single Work Order folder inside the repo")
    args, unknown = parser.parse_known_args()
    if not args.repo and len(unknown) >= 1 and not unknown[0].startswith("-"):
        args.repo = unknown[0]
    if not args.wo and len(unknown) >= 2 and not unknown[1].startswith("-"):
        args.wo = unknown[1]
    return args

CLI_ARGS = parse_cli_args()

def resolve_repositories():
    """Auto-discovers the 6 Software Department repositories on ANY team PC, or targets ONLY --repo if specified."""
    if CLI_ARGS.repo:
        arg_path = os.path.abspath(CLI_ARGS.repo)
        if os.path.isdir(os.path.join(arg_path, ".git")):
            return [arg_path]
        if os.path.isdir(arg_path):
            root_candidates = [arg_path]
        else:
            root_candidates = []
    else:
        root_candidates = []

    env_root = os.environ.get("PALTRO_REPO_ROOT")
    if env_root:
        root_candidates.append(env_root)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    for cfg_candidate in [
        os.path.join(script_dir, "team_local_config.json"),
        os.path.join(script_dir, "paltro-sd01.github.io", "team_local_config.json"),
    ]:
        if os.path.exists(cfg_candidate):
            try:
                with open(cfg_candidate, "r", encoding="utf-8") as cf:
                    c = json.load(cf)
                    if c.get("repo_root"):
                        root_candidates.append(c["repo_root"])
            except Exception:
                pass

    root_candidates.extend([
        os.path.join(script_dir, "Software Repo"),
        os.path.join(os.path.dirname(script_dir), "Software Repo"),
        r"D:\Projects\Software Repo",
        r"C:\Projects\Software Repo",
    ])

    rel_Layouts = [
        ["BOCLE", "LAB-IQ 150", os.path.join("LAB-IQ", "Airjet"), os.path.join("LAB-IQ", "B2V2"), os.path.join("LAB-IQ", "HFRR Adv"), "LAB-IQ 350"],
        ["BOCLE", "LAB-IQ-150", "AIRJET", "B2V2", "HFRR-ADV", "LAB-IQ-350"],
    ]

    for root in root_candidates:
        if not root or not os.path.isdir(root):
            continue
        found = []
        for layout in rel_Layouts:
            for sub in layout:
                p = os.path.join(root, sub)
                if os.path.isdir(p) and p not in found:
                    found.append(p)
        if found:
            return found

    return [
        r"D:\Projects\Software Repo\BOCLE",
        r"D:\Projects\Software Repo\LAB-IQ 150",
        r"D:\Projects\Software Repo\LAB-IQ\Airjet",
        r"D:\Projects\Software Repo\LAB-IQ\B2V2",
        r"D:\Projects\Software Repo\LAB-IQ\HFRR Adv",
        r"D:\Projects\Software Repo\LAB-IQ 350",
    ]

REPOSITORIES = resolve_repositories()

# ---------------------------------------------------------------------------
# Change categories. Each entry: (commit prefix, changelog group title).
# The SAME list drives git-cliff grouping here and the "Category of Change"
# drop-down in the dashboard's Work Order Automator (keep both in sync).
# ---------------------------------------------------------------------------
CATEGORY_GROUPS = [
    ("fix",      "🐛 Bug Fixes"),
    ("ui",       "🖥️ UI & Front Panel Fixes"),
    ("logic",    "⚙️ Core VI Logic & Loop Updates"),
    ("feat",     "🚀 Features & Initial Build"),
    ("hw",       "🔌 Hardware, DAQ & Motor Communication"),
    ("calib",    "🎯 Calibration & PID Tuning"),
    ("report",   "📄 Reports, PDF & Data Logging"),
    ("config",   "🛠️ Config, INI & Settings"),
    ("perf",     "🚄 Performance & Optimization"),
    ("refactor", "♻️ Refactor & Code Cleanup"),
    ("safety",   "🛡️ Safety, Trips & Interlocks"),
    ("test",     "🧫 Test Validation & Verification"),
    ("build",    "📦 Build, EXE & Installer"),
    ("docs",     "📚 Documentation"),
    ("revert",   "⏪ Reverts & Rollbacks"),
]
MISC_GROUP = "📌 Miscellaneous Updates & Modifications"

README_START = "<!-- WO-STATUS:START (auto-generated by update_all_configs.py - do not edit) -->"
README_END = "<!-- WO-STATUS:END -->"


def list_wo_folders(repo_path):
    """Auto-discovers every Work Order folder that exists in the repository."""
    found = []
    for entry in os.listdir(repo_path):
        full_path = os.path.join(repo_path, entry)
        up = entry.upper()
        if os.path.isdir(full_path) and ("WO" in up or "WORKORDER" in up or "EROSION" in up):
            found.append(entry)
    found.sort()
    return found


def get_commit_body(repo_path, commit_hash):
    """Returns the extra lines (body) of a commit message as a list of non-empty lines."""
    res = subprocess.run([GIT_BIN, "log", "-1", "--format=%b", commit_hash], cwd=repo_path,
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
    if res.returncode != 0:
        return []
    return [l.strip() for l in res.stdout.splitlines() if l.strip()]


def strip_commit_prefix(subject):
    """'fix(WO 2485): [CLOSED] text' -> '[CLOSED] text'."""
    return re.sub(r"^[A-Za-z]+(\([^)]*\))?!?:\s*", "", subject).strip()


def md_cell(text):
    return text.replace("|", "\\|")


def extract_change_items(raw_subject, body_lines=None):
    """Splits a commit message (subject + optional body lines, pipe-separated items,
    or numbered '1. ... 2. ...' items) into a clean list of individual change strings."""
    subj = strip_commit_prefix(raw_subject or "")
    stage_prefix = ""
    m_stage = re.match(r"^(\[(?:CLOSED|TESTING|INTEGRATION|REOPENED|IN-DEV|DEV)\])\s*(.*)$", subj, re.I)
    if m_stage:
        stage_prefix = m_stage.group(1).upper() + " "
        subj = m_stage.group(2).strip()

    items = []
    # 1. Pipe-separated changes in subject (e.g. "Change A | Change B | Change C")
    if " | " in subj:
        parts = [p.strip() for p in subj.split(" | ") if p.strip()]
    # 2. Numbered list in subject (e.g. "1. First change 2. Second change 3. Third change")
    elif re.search(r"(?:^|\s)1[\.\)]\s+.+\s+2[\.\)]\s+", subj):
        parts = [p.strip() for p in re.split(r"\s+(?=\d+[\.\)]\s+)", subj) if p.strip()]
    else:
        parts = [subj] if subj else []

    for idx, p in enumerate(parts):
        clean_p = re.sub(r"^[-•*]\s*", "", p).strip()
        if not clean_p:
            continue
        if idx == 0 and stage_prefix and not clean_p.upper().startswith(stage_prefix.strip()):
            clean_p = stage_prefix + clean_p
        items.append(clean_p)

    seen = {re.sub(r"^\d+[\.\)]\s*", "", it).lower().strip() for it in items}
    for b in (body_lines or []):
        for sub_b in (b.split(" | ") if " | " in b else [b]):
            clean_b = re.sub(r"^[-•*]\s*", "", sub_b.strip()).strip()
            if not clean_b or re.match(r"(?i)^co-authored-by:", clean_b):
                continue
            norm = re.sub(r"^\d+[\.\)]\s*", "", clean_b).lower().strip()
            if norm and norm not in seen:
                seen.add(norm)
                items.append(clean_b)

    return items if items else [raw_subject or "Updated work order files"]


def format_items_for_md(items):
    """Formats a list of change items for a Markdown table cell."""
    if not items:
        return "-"
    if len(items) == 1:
        return f"**{md_cell(items[0])}**"
    head = f"**{md_cell(items[0])}**"
    bullets = "".join(f"<br>• {md_cell(it)}" for it in items[1:])
    return head + bullets


def postprocess_wo_changelog(file_path):
    """Expands pipe-separated or numbered change lists inside a git-cliff generated
    WO CHANGELOG.md so every change appears as its own bullet point."""
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    out = []
    pipe_split = re.compile(r"(?<!\\)\|")
    for line in lines:
        s = line.strip()
        if s.startswith("|") and not s.startswith("| :---") and not s.startswith("| Date"):
            cells = pipe_split.split(s)[1:-1]
            if len(cells) >= 4:
                desc_cell = cells[2].strip().replace("\\|", "|")
                raw_parts = [p.strip() for p in desc_cell.split("<br>") if p.strip()]
                first_part = raw_parts[0].replace("**", "").strip() if raw_parts else ""
                extra_parts = [p.lstrip("•").strip() for p in raw_parts[1:] if p.strip()]
                items = extract_change_items(first_part, extra_parts)
                cells[2] = f" {format_items_for_md(items)} "
                line = "|" + "|".join(cells) + "|"
        out.append(line)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def parse_commit_line(line):
    """Parses formatted git log line into a commit dictionary."""
    if not line or not line.strip():
        return None
    parts = line.strip().split("|")
    if len(parts) >= 5:
        return {
            "hash": parts[0],
            "author": parts[1],
            "date": parts[2],
            "timestamp": int(parts[3]) if parts[3].isdigit() else 0,
            "message": "|".join(parts[4:])
        }
    return None

def get_folder_version(repo_path, folder_name):
    """
    Determines accurate LabVIEW version from version folders (e.g. v01, v02, v07) inside the WO folder.
    Whatever the latest one is, that version is returned.
    """
    folder_path = os.path.join(repo_path, folder_name)
    if not os.path.exists(folder_path):
        return "v01"

    # Priority 1: Direct subdirectories of WO folder (e.g., 'v01', 'v02', ..., 'v07' or 'BOCLE - v05', 'BOCLE - v10- 64 BIT')
    direct_versions = []
    try:
        for d in os.listdir(folder_path):
            dp = os.path.join(folder_path, d)
            if not os.path.isdir(dp):
                continue
            m1 = re.match(r"^v(\d+)", d, re.IGNORECASE)
            if m1:
                direct_versions.append(int(m1.group(1)))
                continue
            m2 = re.search(r"[-_\s]v(\d+)", d, re.IGNORECASE)
            if m2:
                direct_versions.append(int(m2.group(1)))
                continue
    except Exception:
        pass

    if direct_versions:
        return f"v{max(direct_versions):02d}"

    # Priority 2: Builds / exe / nested subdirectories inside the folder (avoiding foreign WO copies)
    nested_versions = []
    for root, dirs, files in os.walk(folder_path):
        if ".git" in root or "node_modules" in root:
            continue
        rel = os.path.relpath(root, folder_path)
        parts = rel.split(os.sep)
        if any(p.startswith("WO ") and p != folder_name for p in parts):
            continue
        for d in dirs:
            m = re.match(r"^v(\d+)", d, re.IGNORECASE)
            if m:
                nested_versions.append(int(m.group(1)))
            else:
                m2 = re.search(r"[-_\s]v(\d+)", d, re.IGNORECASE)
                if m2:
                    nested_versions.append(int(m2.group(1)))

    if nested_versions:
        return f"v{max(nested_versions):02d}"

    # Priority 3: VI or EXE files inside the folder
    file_versions = []
    for root, dirs, files in os.walk(folder_path):
        if ".git" in root or "node_modules" in root:
            continue
        rel = os.path.relpath(root, folder_path)
        parts = rel.split(os.sep)
        if any(p.startswith("WO ") and p != folder_name for p in parts):
            continue
        for f in files:
            if f.endswith(".vi") or f.endswith(".exe"):
                m = re.search(r"[-_\s]v0?(\d+)", f, re.IGNORECASE)
                if m:
                    file_versions.append(int(m.group(1)))

    if file_versions:
        return f"v{max(file_versions):02d}"

    return "v01"

def get_latest_commit_for_folder(repo_path, folder_name):
    """
    Finds the latest real commit for a workorder:
    Method 1: File changes within folder (excluding CHANGELOG.md itself)
    Method 2: Commit message mentioning scope (e.g., WO 2485 or WO2485)
    Returns whichever commit is newer.
    """
    candidates = []

    # Method 1: File changes inside the folder
    cmd1 = [
        GIT_BIN, "log", "-1",
        "--format=%h|%an|%ad|%at|%s",
        "--date=format:%Y-%m-%d %H:%M:%S",
        "--", folder_name, ":(exclude)*/CHANGELOG.md", ":(exclude)CHANGELOG.md"
    ]
    res1 = subprocess.run(cmd1, cwd=repo_path, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if res1.returncode == 0 and res1.stdout.strip():
        c1 = parse_commit_line(res1.stdout.strip().splitlines()[0])
        if c1:
            candidates.append(c1)

    # Method 2: Scope search in commit messages
    wo_clean = folder_name.replace(" ", "").upper()
    cmd2 = [
        GIT_BIN, "log", "-1",
        "-i",
        f"--grep={folder_name}", f"--grep={wo_clean}",
        "--format=%h|%an|%ad|%at|%s",
        "--date=format:%Y-%m-%d %H:%M:%S"
    ]
    res2 = subprocess.run(cmd2, cwd=repo_path, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if res2.returncode == 0 and res2.stdout.strip():
        c2 = parse_commit_line(res2.stdout.strip().splitlines()[0])
        if c2:
            candidates.append(c2)

    if not candidates:
        return None

    candidates.sort(key=lambda x: x["timestamp"], reverse=True)
    return candidates[0]

def detect_status(commit_msg):
    """Extracts status tag from commit message."""
    if not commit_msg:
        return ""
    
    msg_upper = commit_msg.upper()
    if "[CLOSED]" in msg_upper:
        return "🔒 CLOSED"
    elif "[REOPENED]" in msg_upper:
        return "🔄 REOPENED"
    elif "[TESTING]" in msg_upper:
        return "🧪 TESTING"
    elif "[INTEGRATION]" in msg_upper:
        return "⚡ INTEGRATION"
    elif "[IN-DEV]" in msg_upper or "[DEV]" in msg_upper:
        return "🛠️ IN-DEV"
    
    return ""

def build_master_changelog(repo_path):
    """Scans all WO folders, gathers latest commits & versions, writes root CHANGELOG.md.
    Returns the collected rows so the README status table can reuse them."""
    wo_folders = list_wo_folders(repo_path)
    rows = []

    markdown_content = """# ⚙️ Master Work Order Consolidated Report

> 📊 **Global Executive Summary**  
> Tracks the latest status, versions, timestamps, and commit updates across all Work Orders in this repository.

| Work Order / Folder | LabVIEW Version | Current Status | Last Commit Hash | Last Commit Date & Time | Latest Commit Summary | Author |
| :--- | :---: | :---: | :---: | :---: | :--- | :---: |
"""

    for folder in wo_folders:
        commit_info = get_latest_commit_for_folder(repo_path, folder)
        version_str = get_folder_version(repo_path, folder)
        if commit_info:
            status = detect_status(commit_info["message"])
            status_cell = f"`{status}`" if status else ""
            body_lines = get_commit_body(repo_path, commit_info["hash"])
            items = extract_change_items(commit_info["message"], body_lines)
            summary = format_items_for_md(items)
            markdown_content += f"| **{folder}** | `{version_str}` | {status_cell} | `{commit_info['hash']}` | {commit_info['date']} | {summary} | `@{commit_info['author']}` |\n"
            rows.append({
                "folder": folder, "version": version_str, "status": status or "ACTIVE",
                "hash": commit_info["hash"], "date": commit_info["date"],
                "subject": items[0], "items": items,
            })
        else:
            markdown_content += f"| **{folder}** | `{version_str}` | | `-` | `-` | *No commit history recorded* | `-` |\n"
            rows.append({
                "folder": folder, "version": version_str, "status": "ACTIVE",
                "hash": "-", "date": "-",
                "subject": "No commit history recorded", "items": ["No commit history recorded"],
            })

    markdown_content += "\n---\n*Report dynamically updated on commit.*"

    root_changelog_path = os.path.join(repo_path, "CHANGELOG.md")
    with open(root_changelog_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"  [Success] Built Master Root CHANGELOG.md with Version column for {len(wo_folders)} Work Orders.")
    return rows


def build_readme_table(rows):
    lines = [
        "| Work Order | Version | Status | Latest Commit | Last Updated | Latest Summary |",
        "| :--- | :---: | :---: | :---: | :---: | :--- |",
    ]
    for r in rows:
        commit = f"`{r['hash']}`" if r["hash"] != "-" else "-"
        summary = format_items_for_md(r.get("items") or [r["subject"]])
        lines.append(f"| **{r['folder']}** | `{r['version']}` | `{r['status']}` | {commit} | {r['date']} | {summary} |")
    return "\n".join(lines)


def update_readme_status(repo_path, rows):
    """Keeps the 'Tracked Work Orders & Status' table in README.md in sync with the repo."""
    readme_path = os.path.join(repo_path, "README.md")
    if not os.path.exists(readme_path):
        print("  [Skipped] No README.md found for status table.")
        return

    with open(readme_path, "r", encoding="utf-8", newline="") as f:
        original = f.read()
    text = original.replace("\r\n", "\n")
    block = f"{README_START}\n{build_readme_table(rows)}\n{README_END}"

    # Normalize heading title so all READMEs explicitly show 'Tracked Work Orders & Status'
    text = re.sub(
        r"^##\s+.*(Tracked Work Orders|Work Order Status|Tracked Software Status).*$",
        "## 📋 Tracked Work Orders & Status",
        text,
        count=1,
        flags=re.M,
    )

    if README_START in text and README_END in text:
        pre, rest = text.split(README_START, 1)
        _, post = rest.split(README_END, 1)
        new_text = pre + block + post
    else:
        m = re.search(r"^##\s+.*Tracked Work Orders & Status.*$", text, re.M)
        if not m:
            print("  [Warning] README.md has no 'Tracked Work Orders' section - status table not updated.")
            return
        start = m.end()
        nxt = re.search(r"^## ", text[start:], re.M)
        end = start + nxt.start() if nxt else len(text)
        section = text[start:end]
        tbl = re.search(r"(?:^\|.*\n?)+", section, re.M)
        if tbl:
            new_section = section[:tbl.start()] + block + "\n" + section[tbl.end():]
        else:
            new_section = "\n\n" + block + "\n" + section
        new_text = text[:start] + new_section + text[end:]

    if "\r\n" in original:
        new_text = new_text.replace("\n", "\r\n")
    if new_text != original:
        with open(readme_path, "w", encoding="utf-8", newline="") as f:
            f.write(new_text)
        print(f"  [Success] README.md 'Tracked Work Orders & Status' updated ({len(rows)} work orders).")
    else:
        print("  [OK] README.md status table already up to date.")


def generate_folder_cliff_config(wo_name, version_tag):
    """
    Generates git-cliff configuration for an individual Work Order folder.
    The FULL commit message (subject + every extra line the engineer typed) is listed.
    """
    parsers = [
        r"""{ message = '(?i)\[skip ci\]', skip = true }""",
        r"""{ message = '(?i)^chore.*rebuild', skip = true }""",
        r"""{ message = '(?i)\[CLOSED\]', group = "🔒 Releases & Closed Milestones" }""",
        r"""{ message = '(?i)\[REOPENED\]', group = "🔄 Reopened Issues & Hotfixes" }""",
    ]
    # New-style categories win over the [TESTING]/[INTEGRATION] stage tags so a
    # "Hardware + Testing" commit is filed under Hardware (the tag stays visible in the text).
    legacy = ("fix", "ui", "logic", "feat")
    for prefix, title in CATEGORY_GROUPS:
        if prefix not in legacy:
            parsers.append("{ message = '(?i)^" + prefix + r"\b', group = " + '"' + title + '" }')
    parsers.append(r"""{ message = '(?i)\[TESTING\]', group = "🧪 Testing & QA Logs" }""")
    parsers.append(r"""{ message = '(?i)\[INTEGRATION\]', group = "⚡ Module Integration & System Tests" }""")
    for prefix, title in CATEGORY_GROUPS:
        if prefix in legacy:
            parsers.append("{ message = '(?i)^" + prefix + r"\b', group = " + '"' + title + '" }')
    parsers.append('{ message = \'.*\', group = "' + MISC_GROUP + '" }')
    parsers_toml = ",\n    ".join(parsers)

    template = r"""[changelog]
header = '''<div align="center">

# 📋 Work Order Detailed History: __WO__
### Version: `__VER__`

**Complete chronological log of modifications, UI updates, bug fixes, and testing notes.**

</div>

---
'''
body = '''
{% for group, commits in commits | group_by(attribute="group") %}
### {{ group }}

| Date & Time | Commit ID | Description | Author |
| :---: | :---: | :--- | :---: |
{% for commit in commits %}{% set lines = commit.message | split(pat="\n") %}{% set subj = lines | first | trim %}{% if subj is matching("^[A-Za-z]+(\([^)]*\))?!?: ") %}{% set parts = subj | split(pat=": ") %}{% set subj = parts | slice(start=1) | join(sep=": ") %}{% endif %}| {{ commit.author.timestamp | date(format="%Y-%m-%d %H:%M:%S") }} | `{{ commit.id | truncate(length=7, end="") }}` | **{{ subj | upper_first | replace(from="|", to="\|") }}**{% for l in lines | slice(start=1) %}{% if l | trim | length > 0 %}<br>• {{ l | trim | replace(from="|", to="\|") }}{% endif %}{% endfor %} | `@{{ commit.author.name }}` |
{% endfor %}
{% endfor %}
---
'''
trim = true

[git]
conventional_commits = false
filter_unconventional = false
ignore_tags = ".*"
include_paths = ["__WO__/**", "__WO__/*"]

commit_parsers = [
    __PARSERS__
]
"""
    return (template.replace("__WO__", wo_name)
                    .replace("__VER__", version_tag)
                    .replace("__PARSERS__", parsers_toml))


def process_repository(repo_path, target_wo=None):
    print(f"\n=========================================")
    print(f" Processing Repository: {repo_path}")
    if target_wo:
        print(f" Scoped Work Order    : {target_wo} (ONLY this Work Order folder will be updated)")
    print(f"=========================================")

    if not os.path.exists(repo_path):
        print("--> [SKIPPED] Directory does not exist.")
        return

    # STEP 1: Build Master Root CHANGELOG.md (includes Version column)
    rows = build_master_changelog(repo_path)

    # STEP 1b: Keep README 'Tracked Work Orders & Status' table in sync
    update_readme_status(repo_path, rows)

    # STEP 2: Build Detailed CHANGELOG.md for Work Order Subfolder(s)
    wo_folders = list_wo_folders(repo_path)
    if target_wo:
        t_clean = target_wo.strip().lower()
        matched = [w for w in wo_folders if w.lower() == t_clean]
        if not matched and os.path.isdir(os.path.join(repo_path, target_wo.strip())):
            matched = [target_wo.strip()]
        wo_folders = matched

    for entry in wo_folders:
        full_path = os.path.join(repo_path, entry)
        folder_cliff_path = os.path.join(full_path, ".cliff.toml")
        folder_changelog_path = os.path.join(full_path, "CHANGELOG.md")
        version_str = get_folder_version(repo_path, entry)

        with open(folder_cliff_path, "w", encoding="utf-8") as f:
            f.write(generate_folder_cliff_config(entry, version_str))

        cmd_folder = [
            GIT_CLIFF_BIN,
            "-c", folder_cliff_path,
            "-o", folder_changelog_path
        ]
        res_folder = subprocess.run(
            cmd_folder,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if os.path.exists(folder_cliff_path):
            os.remove(folder_cliff_path)

        if res_folder.returncode == 0:
            postprocess_wo_changelog(folder_changelog_path)
            print(f"  [Success] Individual Log generated: {entry}/CHANGELOG.md (Version: {version_str})")
        else:
            print(f"  [Error] Failed generating {entry}/CHANGELOG.md: {res_folder.stderr.strip()}")


if __name__ == "__main__":
    for repo in REPOSITORIES:
        process_repository(repo, target_wo=CLI_ARGS.wo)
    print("\nMaster Summary Table, README status tables & Folder Changelogs with Versions Generated Successfully!")
