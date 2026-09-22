# =============================================================================
# run.ps1 - ONE command to run the app (Windows PowerShell 5.1+ / PowerShell 7)
#   1. Check .venv (create it with Python 3.11 if missing or wrong version)
#   2. Install packages from requirements.txt (only when missing / file changed)
#   3. Start the Streamlit app and open the browser at http://localhost:<port>/home
#
# Usage (from the project folder):
#   powershell -ExecutionPolicy Bypass -File .\run.ps1
#   powershell -ExecutionPolicy Bypass -File .\run.ps1 -Port 8600 -NoBrowser -Reinstall
# Stop: Ctrl + C
# =============================================================================
param(
    [int]$Port = 0,
    [switch]$NoBrowser,
    [switch]$Reinstall
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$RequiredVersion = "3.11"
$VenvDir = ".venv"
$ReqFile = "requirements.txt"
$StampFile = Join-Path $VenvDir ".requirements.sha256"

function Write-Step([string]$Message) { Write-Host "[run] $Message" -ForegroundColor Cyan }
function Stop-WithError([string]$Message) {
    Write-Host "[run] ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Get-PythonVersion([string]$Exe, [string[]]$PreArgs) {
    try {
        $version = & $Exe @PreArgs -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0) { return ($version | Select-Object -First 1).Trim() }
    } catch { }
    return $null
}

function Find-SystemPython {
    $candidates = @(
        @{ Exe = "py"; Args = @("-$RequiredVersion") },
        @{ Exe = "python$RequiredVersion"; Args = @() },
        @{ Exe = "python3"; Args = @() },
        @{ Exe = "python"; Args = @() }
    )
    foreach ($candidate in $candidates) {
        if (Get-Command $candidate.Exe -ErrorAction SilentlyContinue) {
            if ((Get-PythonVersion $candidate.Exe $candidate.Args) -eq $RequiredVersion) { return $candidate }
        }
    }
    return $null
}

function Get-VenvPython {
    foreach ($path in @((Join-Path $VenvDir "Scripts\python.exe"), (Join-Path $VenvDir "bin/python"))) {
        if (Test-Path $path) { return (Resolve-Path $path).Path }
    }
    return $null
}

function Test-PortFree([int]$Candidate) {
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $Candidate)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

# ---- 1. Virtual environment -------------------------------------------------
$VenvPython = Get-VenvPython
if ($VenvPython -and (Get-PythonVersion $VenvPython @()) -ne $RequiredVersion) {
    Write-Step "$VenvDir does not use Python $RequiredVersion -> recreating it"
    Remove-Item -Recurse -Force $VenvDir
    $VenvPython = $null
}
if (-not $VenvPython) {
    $SystemPython = Find-SystemPython
    if (-not $SystemPython) {
        Stop-WithError "Python $RequiredVersion not found. Install it from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then run again."
    }
    Write-Step "Creating virtual environment $VenvDir ..."
    & $SystemPython.Exe @($SystemPython.Args) -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { Stop-WithError "Could not create $VenvDir" }
    $VenvPython = Get-VenvPython
    if (-not $VenvPython) { Stop-WithError "Could not find Python inside $VenvDir" }
}

# ---- 2. Packages (reinstalled only when requirements.txt changes) ------------
$ReqHash = (Get-FileHash -Algorithm SHA256 -Path $ReqFile).Hash
$InstalledHash = if (Test-Path $StampFile) { (Get-Content $StampFile -Raw).Trim() } else { "" }
if ($Reinstall -or $InstalledHash -ne $ReqHash) {
    Write-Step "Installing packages from $ReqFile (first run can take a few minutes) ..."
    & $VenvPython -m pip install --upgrade pip --disable-pip-version-check -q
    & $VenvPython -m pip install -r $ReqFile --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) { Stop-WithError "Package installation failed (see the messages above)." }
    Set-Content -Path $StampFile -Value $ReqHash -Encoding ascii
} else {
    Write-Step "Packages are up to date."
}

# ---- 3. Config, folders, port -------------------------------------------------
if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Step "Created .env from .env.example"
}
New-Item -ItemType Directory -Force -Path "data", "logs" | Out-Null

if ($Port -le 0) {
    $Port = 8501
    if (Test-Path ".env") {
        $line = Select-String -Path ".env" -Pattern "^APP_PORT=(\d+)" | Select-Object -Last 1
        if ($line) { $Port = [int]$line.Matches[0].Groups[1].Value }
    }
}
$FirstPort = $Port
while (-not (Test-PortFree $Port)) {
    $Port++
    if ($Port -gt $FirstPort + 50) { Stop-WithError "No free port found from $FirstPort to $Port." }
}
$Url = "http://localhost:$Port/home"

# ---- 4. Open the browser once the server answers ------------------------------
$BrowserJob = $null
if (-not $NoBrowser) {
    $BrowserJob = Start-Job -ArgumentList $Port, $Url -ScriptBlock {
        param($JobPort, $JobUrl)
        for ($i = 0; $i -lt 120; $i++) {
            try {
                $response = Invoke-WebRequest -UseBasicParsing -TimeoutSec 1 -Uri "http://127.0.0.1:$JobPort/_stcore/health"
                if ($response.StatusCode -eq 200) { Start-Process $JobUrl; return }
            } catch { }
            Start-Sleep -Milliseconds 500
        }
    }
}

# ---- 5. Start the app (one Streamlit process) ---------------------------------
Write-Step "Starting app at $Url  (press Ctrl+C to stop)"
try {
    & $VenvPython -m streamlit run "frontend/app.py" --server.port $Port --server.headless true
} finally {
    if ($BrowserJob) { Remove-Job -Job $BrowserJob -Force -ErrorAction SilentlyContinue }
}
