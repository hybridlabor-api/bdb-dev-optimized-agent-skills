# install_daemon.ps1 - Windows Scheduled Task Setup for OpenWiki Daemon (Gemma 4 API)

$UserHome = [System.Environment]::GetFolderPath('UserProfile')
$ScriptPath = "$UserHome\.gemini\config\skills\openwiki-skill\scripts\openwiki_daemon.py"
$DaemonLogDir = "$UserHome\.openwiki"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host " Installing OpenWiki Background Daemon (Windows Task Scheduler)" -ForegroundColor Cyan
Write-Host " Using Gemma 4 Direct API (no agy spawning)" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. Resolve script path
if (-not (Test-Path $ScriptPath)) {
    $ScriptPath = "$PSScriptRoot\openwiki_daemon.py"
    if (-not (Test-Path $ScriptPath)) {
        Write-Error "Error: Cannot find openwiki_daemon.py"
        exit 1
    }
}

# 2. Install Python dependency
Write-Host "Installing google-genai SDK..." -ForegroundColor Yellow
try {
    pip install --quiet google-genai 2>$null
} catch {
    Write-Host "Warning: pip install failed. Install google-genai manually." -ForegroundColor Yellow
}

# 3. Resolve API key
$GeminiKey = $env:GEMINI_API_KEY
if ([string]::IsNullOrWhiteSpace($GeminiKey)) {
    Write-Host ""
    $GeminiKey = Read-Host "Enter your Gemini API key (or press Enter to skip)"
}

if (-not [string]::IsNullOrWhiteSpace($GeminiKey)) {
    Write-Host "Verifying API key..." -ForegroundColor Yellow
    try {
        $VerifyResult = python -c "
from google import genai
client = genai.Client(api_key='$GeminiKey')
r = client.models.generate_content(model='gemma-4-12b-it', contents='Say OK')
print('OK')
" 2>&1
        if ($VerifyResult -match "OK") {
            Write-Host " -> API key verified." -ForegroundColor Green
            [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", $GeminiKey, "User")
        } else {
            Write-Host " -> WARNING: API key verification failed. Daemon will run in collect-only mode." -ForegroundColor Yellow
            $GeminiKey = ""
        }
    } catch {
        Write-Host " -> WARNING: Verification error. Daemon will run in collect-only mode." -ForegroundColor Yellow
        $GeminiKey = ""
    }
} else {
    Write-Host "No API key provided. Daemon will run in collect-only mode." -ForegroundColor Yellow
}

# 4. Ensure log directory
if (-not (Test-Path $DaemonLogDir)) {
    New-Item -ItemType Directory -Force -Path $DaemonLogDir | Out-Null
}

# 5. Build scheduled task action with API key in environment
$EnvSetup = ""
if (-not [string]::IsNullOrWhiteSpace($GeminiKey)) {
    $EnvSetup = "`$env:GEMINI_API_KEY='$GeminiKey'; "
}
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -Command `"& { $EnvSetup python '$ScriptPath' --one-shot }`""

# 6. Trigger: every 2 hours via repetition
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Trigger.Repetition = (New-ScheduledTaskTrigger -Once -At "00:00" -RepetitionInterval (New-TimeSpan -Hours 2)).Repetition

# 7. Settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# 8. Register
$TaskName = "BDB_OpenWiki_Daemon"
Write-Host "Registering task '$TaskName'..." -ForegroundColor Yellow

try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "BDB OpenWiki Daemon - Gemma 4 API documentation generator" -Force | Out-Null
    Write-Host " -> Success! OpenWiki daemon installed (runs every 2 hours)." -ForegroundColor Green
    Write-Host " -> Logs: $DaemonLogDir\daemon.log" -ForegroundColor Green
    Write-Host " -> Projects config: $DaemonLogDir\projects.json" -ForegroundColor Green

    Start-ScheduledTask -TaskName $TaskName
    Write-Host " -> Initial run launched." -ForegroundColor Green
} catch {
    Write-Error "Failed to register Scheduled Task: $_"
}

Write-Host "=========================================================" -ForegroundColor Cyan
