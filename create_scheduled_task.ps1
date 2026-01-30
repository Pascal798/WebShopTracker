<#
create_scheduled_task.ps1

Creates a Windows Scheduled Task that runs the WebShopTracker bot every N minutes.

Usage (run as Administrator):
  .\create_scheduled_task.ps1 -ProjectDir 'C:\Users\SPA\Projects\WebShopTracker' -IntervalMinutes 5 -Force

Parameters:
  -ProjectDir: Path to the project folder (defaults to script folder)
  -TaskName:   Name of the Scheduled Task
  -IntervalMinutes: Repetition interval in minutes (default 5)
  -BotExeRelative: Relative path to the bot executable inside the project (default 'dist\bot\bot.exe')
  -Force:       If set, remove and recreate the task if it already exists
#>

[CmdletBinding()]
param(
    [string]$ProjectDir = $PSScriptRoot,
    [string]$TaskName = "WebShopTrackerBot",
    [int]$IntervalMinutes = 5,
    [string]$BotExeRelative = "dist\bot\bot.exe",
    [switch]$Force
)

Write-Output "ProjectDir: $ProjectDir"
Write-Output "TaskName: $TaskName"
Write-Output "IntervalMinutes: $IntervalMinutes"

$BotExe = Join-Path -Path $ProjectDir -ChildPath $BotExeRelative
if (-not (Test-Path $BotExe)) {
    Write-Error "Bot executable not found at: $BotExe`nPlease run build_exe.bat first to create the executable."
    exit 1
}

# If task exists
try {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
} catch {
    $existing = $null
}

if ($existing) {
    if ($Force) {
        Write-Output "Task '$TaskName' already exists — removing because -Force was provided."
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    } else {
        Write-Output "Task '$TaskName' already exists. Use -Force to recreate. Exiting."
        exit 0
    }
}

# Create action that starts bot.exe with working directory set to its folder
$BotDir = Split-Path $BotExe -Parent

# Use cmd.exe /c start "" /D "<workdir>" "<exe>"
# Build the argument string by concatenation to avoid quoting issues
$escapedBotDir = $BotDir
$escapedBotExe = $BotExe
$argument = '/c start "" /D "' + $escapedBotDir + '" "' + $escapedBotExe + '"'

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $argument

# Create a trigger that starts once immediately and repeats every IntervalMinutes for a long duration
$startTime = (Get-Date).AddMinutes(1)
$repetitionDuration = New-TimeSpan -Days 3650
$trigger = New-ScheduledTaskTrigger -Once -At $startTime -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration $repetitionDuration

# Principal: run as the current user with highest privileges
$user = "$env:USERNAME"
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Description "Runs WebShopTracker bot every $IntervalMinutes minutes" -Force:$Force

Write-Output "Scheduled Task '$TaskName' created to run $BotExe every $IntervalMinutes minutes."
Write-Output "If the task fails to start, run PowerShell as Administrator and re-run this script with -Force."
