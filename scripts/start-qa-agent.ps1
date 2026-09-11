$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$PackageJson = Join-Path $FrontendDir "package.json"

$StateDir = Join-Path $ProjectRoot ".qa-agent"
$LogDir = Join-Path $StateDir "logs"

$BackendPidFile = Join-Path $StateDir "backend.pid"
$FrontendPidFile = Join-Path $StateDir "frontend.pid"

$BackendOutLog = Join-Path $LogDir "backend-out.log"
$BackendErrLog = Join-Path $LogDir "backend-error.log"
$FrontendOutLog = Join-Path $LogDir "frontend-out.log"
$FrontendErrLog = Join-Path $LogDir "frontend-error.log"

$BackendUrl = "http://127.0.0.1:8000/api/health"
$FrontendUrl = "http://127.0.0.1:5173"

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-HttpUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest `
            -Uri $Url `
            -UseBasicParsing `
            -TimeoutSec 2

        return (
            $response.StatusCode -ge 200
            -and
            $response.StatusCode -lt 500
        )
    }
    catch {
        return $false
    }
}

function Show-LogTail {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,

        [Parameter(Mandatory = $true)]
        [string[]]$Paths
    )

    Write-Host ""
    Write-Host "--------------------------------------------" -ForegroundColor DarkGray
    Write-Host $Title -ForegroundColor Yellow
    Write-Host "--------------------------------------------" -ForegroundColor DarkGray

    $Found = $false

    foreach ($Path in $Paths) {
        if (
            (Test-Path $Path)
            -and
            (Get-Item $Path).Length -gt 0
        ) {
            $Found = $true

            Write-Host ""
            Write-Host $Path -ForegroundColor DarkGray

            Get-Content `
                -Path $Path `
                -Tail 20
        }
    }

    if (-not $Found) {
        Write-Host "No log output was created." -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "============================================"
Write-Host "  Website QA Agent"
Write-Host "============================================"
Write-Host ""

if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: .venv Python was not found." -ForegroundColor Red
    Write-Host "Expected: $PythonExe" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $PackageJson)) {
    Write-Host "ERROR: frontend\package.json was not found." -ForegroundColor Red
    Write-Host "Expected: $PackageJson" -ForegroundColor Yellow
    exit 1
}

$NpmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue

if (-not $NpmCommand) {
    $NpmCommand = Get-Command npm -ErrorAction SilentlyContinue
}

if (-not $NpmCommand) {
    Write-Host "ERROR: npm was not found." -ForegroundColor Red
    Write-Host "Node.js/npm must be installed and available in PATH." -ForegroundColor Yellow
    exit 1
}

$NpmExe = $NpmCommand.Source

$BackendReady = Test-HttpUrl -Url $BackendUrl

if ($BackendReady) {
    Write-Host "[OK] Backend is already running." -ForegroundColor Green
}
else {
    Write-Host "[1/2] Starting backend..." -ForegroundColor Cyan

    Remove-Item $BackendOutLog -Force -ErrorAction SilentlyContinue
    Remove-Item $BackendErrLog -Force -ErrorAction SilentlyContinue

    $BackendProcess = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList @(
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000"
        ) `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $BackendOutLog `
        -RedirectStandardError $BackendErrLog `
        -PassThru

    Set-Content `
        -Path $BackendPidFile `
        -Value $BackendProcess.Id
}

$FrontendReady = Test-HttpUrl -Url $FrontendUrl

if ($FrontendReady) {
    Write-Host "[OK] Frontend is already running." -ForegroundColor Green
}
else {
    Write-Host "[2/2] Starting frontend..." -ForegroundColor Cyan

    Remove-Item $FrontendOutLog -Force -ErrorAction SilentlyContinue
    Remove-Item $FrontendErrLog -Force -ErrorAction SilentlyContinue

    $FrontendProcess = Start-Process `
        -FilePath $NpmExe `
        -ArgumentList @(
            "run",
            "dev",
            "--",
            "--host",
            "127.0.0.1",
            "--port",
            "5173",
            "--strictPort"
        ) `
        -WorkingDirectory $FrontendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $FrontendOutLog `
        -RedirectStandardError $FrontendErrLog `
        -PassThru

    Set-Content `
        -Path $FrontendPidFile `
        -Value $FrontendProcess.Id
}

Write-Host ""
Write-Host "Waiting for services..." -ForegroundColor Yellow

for ($Second = 1; $Second -le 45; $Second++) {
    if (-not $BackendReady) {
        $BackendReady = Test-HttpUrl -Url $BackendUrl
    }

    if (-not $FrontendReady) {
        $FrontendReady = Test-HttpUrl -Url $FrontendUrl
    }

    $BackendText = if ($BackendReady) { "READY" } else { "starting" }
    $FrontendText = if ($FrontendReady) { "READY" } else { "starting" }

    Write-Host (
        "`rBackend: {0,-8}  Frontend: {1,-8}  {2,2}s" -f `
        $BackendText,
        $FrontendText,
        $Second
    ) -NoNewline

    if ($BackendReady -and $FrontendReady) {
        break
    }

    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host ""

if (-not $BackendReady) {
    Write-Host "ERROR: Backend did not start." -ForegroundColor Red

    Show-LogTail `
        -Title "Backend log" `
        -Paths @(
            $BackendErrLog,
            $BackendOutLog
        )
}

if (-not $FrontendReady) {
    Write-Host "ERROR: Frontend did not start." -ForegroundColor Red

    Show-LogTail `
        -Title "Frontend log" `
        -Paths @(
            $FrontendErrLog,
            $FrontendOutLog
        )
}

if (
    -not $BackendReady
    -or
    -not $FrontendReady
) {
    Write-Host ""
    Write-Host "Logs are saved in:" -ForegroundColor Yellow
    Write-Host $LogDir
    exit 1
}

Write-Host "[OK] Backend ready:  http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "[OK] Frontend ready: http://127.0.0.1:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Opening Website QA Agent..." -ForegroundColor Cyan

Start-Process $FrontendUrl

Start-Sleep -Seconds 1
exit 0
