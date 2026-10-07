# =============================================================================
# Gravigram - Полный Автономный Установщик для Windows (Zero-to-Hero)
# Автоматически проверяет и устанавливает: Python 3.11 (через winget или python.org),
# создает venv, ставит зависимости, распаковывает веб-приложение и запускает мастер.
# =============================================================================

param(
    [string]$RepoUrl = "https://github.com/kobaltgit/gravigram.git",
    [string]$TargetDir = "gravigram"
)

$ErrorActionPreference = "Stop"

if ($MyInvocation.MyCommand.Path) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $ScriptDir
}

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "         🚀 GRAVIGRAM - АВТОМАТИЧЕСКАЯ УСТАНОВКА ПОД КЛЮЧ             " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 0. Автоматическое клонирование репозитория, если скрипт запущен вне каталога проекта
if (-not (Test-Path "run.py") -or -not (Test-Path "requirements.txt")) {
    Write-Host "[*] Скрипт запущен вне существующего каталога проекта." -ForegroundColor Yellow
    if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
        $RepoUrl = Read-Host "Введите Git URL репозитория (например, https://github.com/username/antigravity_bot.git)"
    }
    
    if (-not [string]::IsNullOrWhiteSpace($RepoUrl)) {
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Host "❌ Утилита git не найдена в системе. Установите git: winget install Git.Git" -ForegroundColor Red
            exit 1
        }
        Write-Host "[*] Клонирование репозитория из $RepoUrl в $TargetDir..." -ForegroundColor Yellow
        git clone $RepoUrl $TargetDir
        Set-Location $TargetDir
        Write-Host "✔ Репозиторий успешно склонирован." -ForegroundColor Green
    } else {
        Write-Host "❌ Адрес репозитория не указан." -ForegroundColor Red
        exit 1
    }
}

# 1. Функция поиска Python 3.10+
function Get-CompatiblePython {
    $pythonCandidates = @("python", "py")
    
    # Также проверяем стандартные директории установки на Windows
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

# 2. Авто-установка Python при отсутствии
$PythonCmd = Get-CompatiblePython

if (-not $PythonCmd) {
    Write-Host "[*] Python 3.10+ не найден на компьютере. Запуск автоматической установки..." -ForegroundColor Yellow

    if (Get-Command "winget" -ErrorAction SilentlyContinue) {
        Write-Host "--> Установка Python 3.11 через Windows Package Manager (winget)..." -ForegroundColor Cyan
        try {
            winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
        } catch {
            Write-Host "⚠️ Сбой winget, пробуем прямое скачивание с python.org..." -ForegroundColor Yellow
        }
    }

    $PythonCmd = Get-CompatiblePython

    if (-not $PythonCmd) {
        Write-Host "--> Скачивание официального установщика Python 3.11 с python.org..." -ForegroundColor Cyan
        $installerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        $installerPath = Join-Path $env:TEMP "python-3.11.9-amd64.exe"
        
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
        
        Write-Host "--> Выполнение тихой установки Python 3.11 (с добавлением в системный PATH)..." -ForegroundColor Cyan
        $process = Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait -PassThru
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
    }

    # Обновление путей PATH в текущей сессии PowerShell
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    $PythonCmd = Get-CompatiblePython
}

if (-not $PythonCmd) {
    Write-Host "❌ Ошибка: Не удалось обнаружить Python после установки. Пожалуйста, перезапустите PowerShell." -ForegroundColor Red
    exit 1
}

Write-Host "✔ Найден совместимый Python: $PythonCmd" -ForegroundColor Green

# 3. Создание виртуального окружения venv
$VenvDir = Join-Path $ScriptDir "venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[*] Создание виртуального окружения (venv)..." -ForegroundColor Yellow
    & $PythonCmd -m venv $VenvDir
    Write-Host "✔ Виртуальное окружение venv создано." -ForegroundColor Green
}

# 4. Установка зависимостей Python
Write-Host "[*] Установка зависимостей Python из requirements.txt..." -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install -r requirements.txt --quiet
Write-Host "✔ Библиотеки Python успешно установлены." -ForegroundColor Green

# 5. Проверка и автоматическая распаковка Flutter Web Mini App
$WebIndex = Join-Path $ScriptDir "frontend_flutter\build\web\index.html"
$TarArchive = Join-Path $ScriptDir "miniapp_web.tar.gz"

if ((-not (Test-Path $WebIndex)) -and (Test-Path $TarArchive)) {
    Write-Host "[*] Распаковка готового веб-бандла Telegram Mini App..." -ForegroundColor Yellow
    & $VenvPython -c "import tarfile, os; os.makedirs('frontend_flutter/build', exist_ok=True); tarfile.open('miniapp_web.tar.gz').extractall('frontend_flutter/build')"
    if (Test-Path $WebIndex) {
        Write-Host "✔ Веб-приложение Mini App готово к работе." -ForegroundColor Green
    }
# 6. Проверка и автоматическая установка Antigravity CLI (agy)
$agyCmd = Get-Command "agy" -ErrorAction SilentlyContinue
$localAgy = Join-Path $env:LOCALAPPDATA "agy\bin\agy.EXE"
if ((-not $agyCmd) -and (-not (Test-Path $localAgy))) {
    Write-Host "[*] Antigravity CLI (agy) не найден. Запуск официального установщика..." -ForegroundColor Yellow
    try {
        irm https://antigravity.google/cli/install.ps1 | iex
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        Write-Host "✔ Antigravity CLI (agy) успешно установлен!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Не удалось автоматически загрузить agy. Вы сможете установить его позже вручную." -ForegroundColor Yellow
    }
}

# 7. Запуск интерактивного мастера настройки (.env, БД, токены)
Write-Host ""
& $VenvPython setup.py
