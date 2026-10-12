# Paltro-SD01 Engineering & Git Operations Command Center

Live Production URL: **[https://paltro-sd01.github.io](https://paltro-sd01.github.io)**

Interactive, presentation-ready Web Dashboard and Work Order Release Suite for all 6 industrial rig repositories under **[github.com/Paltro-SD01](https://github.com/Paltro-SD01)**:
- [LAB-IQ-150](https://github.com/Paltro-SD01/LAB-IQ-150)
- [BOCLE](https://github.com/Paltro-SD01/BOCLE)
- [HFRR-ADV](https://github.com/Paltro-SD01/HFRR-ADV)
- [LAB-IQ-350](https://github.com/Paltro-SD01/LAB-IQ-350)
- [B2V2](https://github.com/Paltro-SD01/B2V2)
- [AIRJET](https://github.com/Paltro-SD01/AIRJET)

---

## 🌐 Public Access

Access the dashboard from anywhere across any browser, phone, or laptop:
👉 **[https://paltro-sd01.github.io](https://paltro-sd01.github.io)**

---

## 🛠️ Workstation Usage & Syncing New Commits

Whenever you push new code or close work orders in your LabVIEW rigs, update and republish the dashboard in one step:

```powershell
# 1. Navigate to the dashboard repository
Set-Location "D:\Projects\paltro-sd01.github.io"

# 2. Rescan all 6 local rig repos and regenerate data.js
python refresh_data.py

# 3. Commit and push the updated stats to GitHub Pages
git add data.js
git commit -m "chore: sync latest repo commits and work orders"
git push origin main
```
Your live dashboard at `https://paltro-sd01.github.io` updates automatically within 30 seconds!

---

## 💻 Local Testing Server
To view locally or test on your local office network:
```powershell
python "D:\Projects\paltro-sd01.github.io\serve.py"
```
- Local URL: `http://localhost:8000/index.html`
- LAN (Wi-Fi) URL: `http://192.168.0.63:8000/index.html`
