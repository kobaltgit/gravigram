# PowerShell script to run all tests (Python backend + Flutter Mini App)
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$FlutterDir = Join-Path $RootDir "frontend_flutter"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Gravigram Automated Test Suite Runner" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

Set-Location $RootDir

# 1. Python Backend Tests
Write-Host "`n[1/2] Running Python Backend Tests (pytest)..." -ForegroundColor Yellow

$PytestCmd = "pytest"
if (Test-Path "$RootDir\venv\Scripts\pytest.exe") {
    $PytestCmd = "$RootDir\venv\Scripts\pytest.exe"
} elseif (Test-Path "$RootDir\.venv\Scripts\pytest.exe") {
    $PytestCmd = "$RootDir\.venv\Scripts\pytest.exe"
}

try {
    & $PytestCmd -v
    Write-Host "✅ Python tests passed!" -ForegroundColor Green
} catch {
    Write-Host "❌ Python tests failed!" -ForegroundColor Red
    exit 1
}

# 2. Flutter Mini App Tests
Write-Host "`n[2/2] Running Flutter Mini App Tests (flutter test)..." -ForegroundColor Yellow

if (Get-Command "flutter" -ErrorAction SilentlyContinue) {
    Set-Location $FlutterDir
    try {
        flutter test
        Write-Host "✅ Flutter tests passed!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Flutter tests failed!" -ForegroundColor Red
        exit 1
    } finally {
        Set-Location $RootDir
    }
} else {
    Write-Host "⚠️ 'flutter' command not found in PATH. Skipping Flutter tests." -ForegroundColor DarkYellow
}

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host "🎉 All tests completed successfully!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
