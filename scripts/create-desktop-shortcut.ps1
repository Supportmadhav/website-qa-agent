$ErrorActionPreference = "Stop"

try {
    $ProjectRoot = Split-Path -Parent $PSScriptRoot
    $TargetBat = Join-Path $ProjectRoot "Start Website QA Agent.bat"

    if (-not (Test-Path $TargetBat)) {
        throw "Start Website QA Agent.bat was not found at: $TargetBat"
    }

    $Desktop = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $Desktop "Website QA Agent.lnk"

    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)

    $Shortcut.TargetPath = $TargetBat
    $Shortcut.WorkingDirectory = $ProjectRoot
    $Shortcut.Description = "Start Website QA Agent"
    $Shortcut.WindowStyle = 7

    $Shortcut.Save()

    Write-Host ""
    Write-Host "Desktop shortcut created successfully." -ForegroundColor Green
    Write-Host ""
    Write-Host "Shortcut:" -ForegroundColor Cyan
    Write-Host $ShortcutPath
    Write-Host ""
    Write-Host "From now on, double-click 'Website QA Agent' on your Desktop." -ForegroundColor Yellow

    exit 0
}
catch {
    Write-Host ""
    Write-Host "ERROR: Could not create desktop shortcut." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow

    exit 1
}
