$ErrorActionPreference = "SilentlyContinue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$StateDir = Join-Path $ProjectRoot ".qa-agent"

$PidFiles = @(
    (Join-Path $StateDir "backend.pid"),
    (Join-Path $StateDir "frontend.pid")
)

Write-Host ""
Write-Host "Stopping Website QA Agent..." -ForegroundColor Yellow

foreach ($PidFile in $PidFiles) {
    if (-not (Test-Path $PidFile)) {
        continue
    }

    $ProcessId = Get-Content $PidFile -ErrorAction SilentlyContinue

    if ($ProcessId) {
        Get-CimInstance Win32_Process `
            -ErrorAction SilentlyContinue |
            Where-Object {
                $_.ParentProcessId -eq [int]$ProcessId
            } |
            ForEach-Object {
                Stop-Process `
                    -Id $_.ProcessId `
                    -Force `
                    -ErrorAction SilentlyContinue
            }

        Stop-Process `
            -Id $ProcessId `
            -Force `
            -ErrorAction SilentlyContinue
    }

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

foreach ($Port in @(8000, 5173)) {
    $Connections = Get-NetTCPConnection `
        -LocalPort $Port `
        -State Listen `
        -ErrorAction SilentlyContinue

    foreach ($Connection in $Connections) {
        if (
            $Connection.OwningProcess
            -and
            $Connection.OwningProcess -ne $PID
        ) {
            Stop-Process `
                -Id $Connection.OwningProcess `
                -Force `
                -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "Website QA Agent stopped." -ForegroundColor Green
