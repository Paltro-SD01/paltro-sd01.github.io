# Paltro-SD01 Engineering & Git Operations Command Center

Interactive, presentation-ready Web Dashboard for all 6 industrial rig repositories under **[github.com/Paltro-SD01](https://github.com/Paltro-SD01)**.

---

## 🌟 Key Features

1. **Unified Multi-Repo Dashboard:**
   - [LAB-IQ-150](https://github.com/Paltro-SD01/LAB-IQ-150)
   - [BOCLE](https://github.com/Paltro-SD01/BOCLE)
   - [HFRR-ADV](https://github.com/Paltro-SD01/HFRR-ADV)
   - [LAB-IQ-350](https://github.com/Paltro-SD01/LAB-IQ-350)
   - [B2V2](https://github.com/Paltro-SD01/B2V2)
   - [AIRJET](https://github.com/Paltro-SD01/AIRJET)

2. **Commit & Push Statistical Reports:**
   - Total commit counters & breakdown per repository.
   - Interactive Chart.js visual graphs for commit velocity and tagged releases.
   - Work order lifecycle doughnut chart (Closed / In Dev / Testing / Discontinued).

3. **Changelog & Work Orders Consolidated Tracker:**
   - Consolidates work orders (e.g. `WO 2476`, `WO 2485`, `WO 2480`, `WO 2394`, etc.).
   - Displays real-time milestone states (`CLOSED`, `TESTING`, `ACTIVE`).
   - Shows latest commit hash, timestamp, and author details.

4. **Local Drive to Remote Git Path Mapping:**
   - Displays the exact local workstation path (e.g., `D:\Projects\Software Repo\...`) from which code was developed and pushed.
   - Shows remote Git push remotes (`git@github.com:Paltro-SD01/...`).

5. **Version Control & Tag Tracking:**
   - Visual inspection of the latest production release tag (e.g., `WO2476-CLOSED-20261012-131550`, `WO2485-CLOSED-20260930-145929`).
   - Live commit stream with modified file diff inspector.

---

## 🚀 Quick Launch

### Option 1: Direct File Open
Double click or open directly in Chrome/Edge:
```
C:\Users\Admin\.gemini\antigravity\scratch\github-dashboard\index.html
```

### Option 2: Run Local Web Server
Open PowerShell in this directory and run:
```powershell
python serve.py
```
This opens `http://localhost:8080/index.html` automatically in your browser.

### Option 3: Refresh Data After New Commits
Whenever you push new commits or create new tags in any repository:
```powershell
python refresh_data.py
```
It reads all git histories and work order changelogs, updating `data.js` instantly.

---

## 🌐 Sharing with Stakeholders / Customers
You can host this standalone static folder (`index.html` + `data.js`) on:
- **GitHub Pages** (free public/private webpage via `gh-pages` branch)
- **Netlify / Vercel** (drag-and-drop folder)
- Local network intranet server
