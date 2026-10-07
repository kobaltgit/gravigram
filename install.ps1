# =============================================================================
# Gravigram - Automated All-in-One Installer for Windows (Zero-to-Hero)
# Automatically checks and installs: Python 3.11 (via winget or python.org),
# creates venv, installs dependencies, unpacks Mini App bundle, and runs wizard.
# Supports English and Russian (English by default, with switcher).
# =============================================================================

param(
    [string]$RepoUrl = "https://github.com/kobaltgit/gravigram.git",
    [string]$TargetDir = "gravigram",
    [string]$Language = ""
)

$ErrorActionPreference = "Stop"

if ($MyInvocation.MyCommand.Path) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $ScriptDir
}

# Interactive language selector if not passed as parameter
if (-not $Language) {
    Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  🌐 Select Language / Выберите язык:                                     ║" -ForegroundColor Cyan
    Write-Host "║     [1] English (default)                                                ║" -ForegroundColor Cyan
    Write-Host "║     [2] Русский                                                          ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    $langInput = Read-Host "Choice / Выбор [1]"
    if ($langInput -match "^2|^ru|^RU|^рус") {
        $Language = "ru"
    } else {
        $Language = "en"
    }
}

function Write-Msg([string]$en, [string]$ru, [System.ConsoleColor]$color = [System.ConsoleColor]::White) {
    $text = if ($Language -eq "ru") { $ru } else { $en }
    Write-Host $text -ForegroundColor $color
}

Write-Host "======================================================================" -ForegroundColor Cyan
if ($Language -eq "ru") {
    Write-Host "         🚀 GRAVIGRAM - АВТОМАТИЧЕСКАЯ УСТАНОВКА ПОД КЛЮЧ             " -ForegroundColor Cyan
} else {
    Write-Host "         🚀 GRAVIGRAM - AUTOMATED ALL-IN-ONE INSTALLER                " -ForegroundColor Cyan
}
Write-Host "======================================================================" -ForegroundColor Cyan

# 0. Clone repository if run from outside project directory
if (-not (Test-Path "run.py") -or -not (Test-Path "requirements.txt")) {
    Write-Msg "[*] Script is running outside an existing project directory." "[*] Скрипт запущен вне существующего каталога проекта." Yellow
    if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
        $promptText = if ($Language -eq "ru") { "Введите Git URL репозитория (например, https://github.com/kobaltgit/gravigram.git)" } else { "Enter Git repository URL (e.g. https://github.com/kobaltgit/gravigram.git)" }
        $RepoUrl = Read-Host $promptText
    }
    
    if (-not [string]::IsNullOrWhiteSpace($RepoUrl)) {
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Msg "❌ Git not found in system. Install git: winget install Git.Git" "❌ Утилита git не найдена в системе. Установите git: winget install Git.Git" Red
            exit 1
        }
        Write-Msg "[*] Cloning repository from $RepoUrl into $TargetDir..." "[*] Клонирование репозитория из $RepoUrl в $TargetDir..." Yellow
        git clone $RepoUrl $TargetDir
        Set-Location $TargetDir
        Write-Msg "✔ Repository cloned successfully." "✔ Репозиторий успешно склонирован." Green
    } else {
        Write-Msg "❌ Repository URL not specified." "❌ Адрес репозитория не указан." Red
        exit 1
    }
}

# 1. Search for Python 3.10+
function Get-CompatiblePython {
    $pythonCandidates = @("python", "py")
    
    $commonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Program Files\Python312\python.exe",
        "C:\Program Files\Python311\python.exe",
        "C:\Program Files\Python310\python.exe"
    )

    foreach ($cmd in $pythonCandidates) {
        $cmdInfo = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($cmdInfo) {
            try {
                $ver = & $cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>$null
                $parts = $ver.Split(".")
                if ([int]$parts[0] -ge 3 -and [int]$parts[1] -ge 10) {
                    return $cmd
                }
            } catch {}
        }
    }

    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            try {
                $ver = & $path -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>$null
                $parts = $ver.Split(".")
                if ([int]$parts[0] -ge 3 -and [int]$parts[1] -ge 10) {
                    return $path
                }
            } catch {}
        }
    }

    return $null
}

# 2. Auto-install Python if missing
$PythonCmd = Get-CompatiblePython

if (-not $PythonCmd) {
    Write-Msg "[*] Python 3.10+ not found. Starting automatic installation..." "[*] Python 3.10+ не найден на компьютере. Запуск автоматической установки..." Yellow

    if (Get-Command "winget" -ErrorAction SilentlyContinue) {
        Write-Msg "--> Installing Python 3.11 via Windows Package Manager (winget)..." "--> Установка Python 3.11 через Windows Package Manager (winget)..." Cyan
        try {
            winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
        } catch {
            Write-Msg "⚠️ winget failed, trying direct download from python.org..." "⚠️ Сбой winget, пробуем прямое скачивание с python.org..." Yellow
        }
    }

    $PythonCmd = Get-CompatiblePython

    if (-not $PythonCmd) {
        Write-Msg "--> Downloading official Python 3.11 installer from python.org..." "--> Скачивание официального установщика Python 3.11 с python.org..." Cyan
        $installerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        $installerPath = Join-Path $env:TEMP "python-3.11.9-amd64.exe"
        
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
        
        Write-Msg "--> Executing silent installation of Python 3.11 (adding to system PATH)..." "--> Выполнение тихой установки Python 3.11 (с добавлением в системный PATH)..." Cyan
        $process = Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait -PassThru
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
    }

    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    $PythonCmd = Get-CompatiblePython
}

if (-not $PythonCmd) {
    Write-Msg "❌ Error: Could not detect Python after installation. Please restart PowerShell." "❌ Ошибка: Не удалось обнаружить Python после установки. Пожалуйста, перезапустите PowerShell." Red
    exit 1
}

Write-Msg "✔ Compatible Python found: $PythonCmd" "✔ Найден совместимый Python: $PythonCmd" Green

# 3. Create virtual environment venv
$VenvDir = Join-Path $ScriptDir "venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Msg "[*] Creating virtual environment (venv)..." "[*] Создание виртуального окружения (venv)..." Yellow
    & $PythonCmd -m venv $VenvDir
    Write-Msg "✔ Virtual environment (venv) created." "✔ Виртуальное окружение venv создано." Green
}

# 4. Install Python dependencies
Write-Msg "[*] Installing Python dependencies from requirements.txt..." "[*] Установка зависимостей Python из requirements.txt..." Yellow
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install -r requirements.txt --quiet
Write-Msg "✔ Python libraries installed successfully." "✔ Библиотеки Python успешно установлены." Green

# 5. Check and unpack Flutter Web Mini App
$WebIndex = Join-Path $ScriptDir "frontend_flutter\build\web\index.html"
$TarArchive = Join-Path $ScriptDir "miniapp_web.tar.gz"

if ((-not (Test-Path $WebIndex)) -and (Test-Path $TarArchive)) {
    Write-Msg "[*] Unpacking Telegram Mini App pre-built web bundle..." "[*] Распаковка готового веб-бандла Telegram Mini App..." Yellow
    & $VenvPython -c "import tarfile, os, shutil; os.makedirs('frontend_flutter/build/web', exist_ok=True); tar = tarfile.open('miniapp_web.tar.gz'); has_web = any(m.name.startswith('web/') for m in tar.getmembers()); target = 'frontend_flutter/build' if has_web else 'frontend_flutter/build/web'; tar.extractall(target); tar.close()"
    if (Test-Path $WebIndex) {
        Write-Msg "✔ Telegram Mini App web bundle is ready." "✔ Веб-приложение Mini App готово к работе." Green
    }
}

# 6. Check and install Antigravity CLI (agy)
$agyCmd = Get-Command "agy" -ErrorAction SilentlyContinue
$localAgy = Join-Path $env:LOCALAPPDATA "agy\bin\agy.EXE"
if ((-not $agyCmd) -and (-not (Test-Path $localAgy))) {
    Write-Msg "[*] Antigravity CLI (agy) not found. Running official installer..." "[*] Antigravity CLI (agy) не найден. Запуск официального установщика..." Yellow
    try {
        irm https://antigravity.google/cli/install.ps1 | iex
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        Write-Msg "✔ Antigravity CLI (agy) installed successfully!" "✔ Antigravity CLI (agy) успешно установлен!" Green
    } catch {
        Write-Msg "⚠️ Failed to automatically download agy. You can install it manually later." "⚠️ Не удалось автоматически загрузить agy. Вы сможете установить его позже вручную." Yellow
    }
}

# 7. Run setup wizard
Write-Host ""
& $VenvPython setup.py --lang $Language
