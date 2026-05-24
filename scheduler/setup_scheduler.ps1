# Setup Windows Task Scheduler to run the trading bot automatically.
#
# Usage (in PowerShell, as your normal user - admin not required):
#     cd C:\Users\<you>\Desktop\trading-bot
#     powershell -ExecutionPolicy Bypass -File .\scheduler\setup_scheduler.ps1
#
# Creates two tasks:
#   1. TradingBot-MorningBrief   - runs every weekday at 07:00 Bangkok
#   2. TradingBot-EveningBrief   - runs every weekday at 22:00 Bangkok (pre-US-open)
#
# To remove later:
#     Unregister-ScheduledTask -TaskName "TradingBot-MorningBrief" -Confirm:$false
#     Unregister-ScheduledTask -TaskName "TradingBot-EveningBrief" -Confirm:$false

$ErrorActionPreference = "Stop"

# Resolve project dir relative to this script's location
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PythonExe  = Join-Path $ProjectDir "venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python venv not found at $PythonExe" -ForegroundColor Red
    Write-Host "Run 'python -m venv venv' first inside the project folder."
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "main.py" -WorkingDirectory $ProjectDir

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Morning brief: 07:00 weekdays
$MorningTrigger = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday `
    -At 07:00

Register-ScheduledTask -TaskName "TradingBot-MorningBrief" `
    -Description "Morning market brief - runs main.py and pushes to Telegram" `
    -Action $Action -Trigger $MorningTrigger `
    -Settings $Settings -Principal $Principal -Force | Out-Null

Write-Host "Created: TradingBot-MorningBrief at 07:00 weekdays" -ForegroundColor Green

# Evening brief: 22:00 weekdays (30 min before US open at 22:30 Bangkok time)
$EveningTrigger = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday `
    -At 22:00

Register-ScheduledTask -TaskName "TradingBot-EveningBrief" `
    -Description "Evening market brief - before US market open" `
    -Action $Action -Trigger $EveningTrigger `
    -Settings $Settings -Principal $Principal -Force | Out-Null

Write-Host "Created: TradingBot-EveningBrief at 22:00 weekdays" -ForegroundColor Green

Write-Host ""
Write-Host "Done. To verify:" -ForegroundColor Cyan
Write-Host "  Get-ScheduledTask | Where-Object { `$_.TaskName -like 'TradingBot-*' }"
Write-Host ""
Write-Host "To run immediately for testing:"
Write-Host "  Start-ScheduledTask -TaskName 'TradingBot-MorningBrief'"
