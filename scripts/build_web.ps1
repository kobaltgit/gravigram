# PowerShell script to build Flutter Web Mini App on Windows
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$FlutterDir = Join-Path $RootDir "frontend_flutter"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Building Antigravity Flutter Web Mini App" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

if (-not (Get-Command "flutter" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: 'flutter' command not found in PATH." -ForegroundColor Red
    Write-Host "Please install Flutter SDK (>=3.20) or ensure it is added to your PATH environment variable."
    exit 1
}

Set-Location $FlutterDir

Write-Host "--> Running 'flutter pub get'..." -ForegroundColor Yellow
flutter pub get

Write-Host "--> Building Flutter Web (release mode)..." -ForegroundColor Yellow
flutter build web --release

Write-Host ""
Write-Host "✅ Build completed successfully!" -ForegroundColor Green
Write-Host "Web build located at: $FlutterDir\build\web" -ForegroundColor Green
Set-Location $RootDir
