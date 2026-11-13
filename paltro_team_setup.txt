# ==============================================================================
# PALTRO-SD01 | MULTI-PC TEAM ECOSYSTEM ONBOARDING & AUTO-SYNC SCRIPT
# Run this script on any new Engineering PC (PC 1 .. PC 6) to join the ecosystem.
# ==============================================================================
param(
    [string]$EngineerName = $env:USERNAME,
    [string]$Department   = "SOFTWARE",
    [string]$WorkspaceRoot = $(if (Test-Path "D:\") { "D:\Projects\Software Repo" } else { "C:\Projects\Software Repo" })
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  PALTRO-SD01 | MULTI-PC ENGINEERING ECOSYSTEM SETUP" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Engineer   : $EngineerName" -ForegroundColor Green
Write-Host "PC Name    : $env:COMPUTERNAME" -ForegroundColor Green
Write-Host "Department : $Department" -ForegroundColor Green
Write-Host "Repo Root  : $WorkspaceRoot" -ForegroundColor Yellow

# 1. Create folder structure
New-Item -ItemType Directory -Force -Path $WorkspaceRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $WorkspaceRoot "LAB-IQ") | Out-Null
$ParentDir = Split-Path -Parent $WorkspaceRoot

# 2. Install git-cliff if missing
if (-not (Get-Command "git-cliff" -ErrorAction SilentlyContinue)) {
    Write-Host "`n[1/4] Checking git-cliff changelog generator..." -ForegroundColor Cyan
    winget install --id orhun.git-cliff -e --accept-source-agreements --accept-package-agreements
}

# 3. Clone or Pull all 6 Software Department Repositories
$Repos = @(
    @{ Name = "LAB-IQ-150"; Url = "https://github.com/Paltro-SD01/LAB-IQ-150.git"; Path = (Join-Path $WorkspaceRoot "LAB-IQ 150") },
    @{ Name = "BOCLE";      Url = "https://github.com/Paltro-SD01/BOCLE.git";      Path = (Join-Path $WorkspaceRoot "BOCLE") },
    @{ Name = "HFRR-ADV";   Url = "https://github.com/Paltro-SD01/HFRR-ADV.git";   Path = (Join-Path $WorkspaceRoot "LAB-IQ\HFRR Adv") },
    @{ Name = "LAB-IQ-350"; Url = "https://github.com/Paltro-SD01/LAB-IQ-350.git"; Path = (Join-Path $WorkspaceRoot "LAB-IQ 350") },
    @{ Name = "B2V2";       Url = "https://github.com/Paltro-SD01/B2V2.git";       Path = (Join-Path $WorkspaceRoot "LAB-IQ\B2V2") },
    @{ Name = "AIRJET";     Url = "https://github.com/Paltro-SD01/AIRJET.git";     Path = (Join-Path $WorkspaceRoot "LAB-IQ\Airjet") }
)

Write-Host "`n[2/4] Synchronizing Software Department Repositories..." -ForegroundColor Cyan
foreach ($r in $Repos) {
    if (Test-Path (Join-Path $r.Path ".git")) {
        Write-Host "  -> Pulling latest $($r.Name) at $($r.Path)..." -ForegroundColor Gray
        git -C $r.Path pull origin main --rebase --autostash
    } else {
        Write-Host "  -> Cloning $($r.Name) into $($r.Path)..." -ForegroundColor Green
        git clone $r.Url $r.Path
    }
}

# 4. Clone or Pull Dashboard & Automation Scripts
$DashPath = Join-Path $ParentDir "paltro-sd01.github.io"
Write-Host "`n[3/4] Synchronizing Command Center & Automation Scripts..." -ForegroundColor Cyan
if (Test-Path (Join-Path $DashPath ".git")) {
    git -C $DashPath pull origin main --rebase --autostash
} else {
    git clone "https://github.com/Paltro-SD01/paltro-sd01.github.io.git" $DashPath
}

# Copy portable update_all_configs.py to ParentDir
if (Test-Path (Join-Path $DashPath "update_all_configs.py")) {
    Copy-Item (Join-Path $DashPath "update_all_configs.py") (Join-Path $ParentDir "update_all_configs.py") -Force
}

# 5. Write local PC configuration (path-independent!)
$LocalConfig = @{
    engineer_name = $EngineerName
    pc_name       = $env:COMPUTERNAME
    department    = $Department
    repo_root     = $WorkspaceRoot
    dashboard_dir = $DashPath
    configured_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
} | ConvertTo-Json -Depth 3

Set-Content -Path (Join-Path $DashPath "team_local_config.json") -Value $LocalConfig -Encoding UTF8
Set-Content -Path (Join-Path $ParentDir "team_local_config.json") -Value $LocalConfig -Encoding UTF8
[Environment]::SetEnvironmentVariable("PALTRO_REPO_ROOT", $WorkspaceRoot, "User")

# 6. Register this PC in the Cloud Device & Team Audit Log
Write-Host "`n[4/4] Registering Workstation $env:COMPUTERNAME in GitHub Ecosystem..." -ForegroundColor Cyan
$Beacon = @{
    timestamp   = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    device_id   = "PC-$env:COMPUTERNAME"
    device_name = "$EngineerName ($env:COMPUTERNAME)"
    platform    = "Windows Workstation ($Department Dept)"
    app_mode    = "Team Workstation Node"
    resolution  = "Workstation CLI"
    network     = $WorkspaceRoot
    sync_id     = "TEAM-ONBOARD"
    event       = "Onboarded Team PC ($Department Dept)"
} | ConvertTo-Json -Compress

try {
    Invoke-RestMethod -Uri "https://ntfy.sh/paltro_sd01_device_log_84f29a1c" -Method Post -Body $Beacon | Out-Null
} catch {}

Write-Host "`n✅ Setup Complete! Your PC ($env:COMPUTERNAME) is now connected to the Paltro-SD01 Ecosystem." -ForegroundColor Green
Write-Host "   Open https://paltro-sd01.github.io to view the Team Roster & Release Matrix." -ForegroundColor Cyan
