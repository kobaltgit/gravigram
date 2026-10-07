#!/usr/bin/env bash
# =============================================================================
# Gravigram - Automated All-in-One Installer (Zero-to-Hero)
# Automatically installs: Python 3.10+, pip, venv, curl, git, tar, ffmpeg,
# configures environment, unpacks Mini App bundle, and runs setup wizard.
# Supports English and Russian (English by default, with switcher).
# =============================================================================

set -e

# Terminal Colors
CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
RESET='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse CLI arguments for language
SETUP_LANG=""
for arg in "$@"; do
    case "$arg" in
        -l=*|--lang=*) SETUP_LANG="${arg#*=}" ;;
        -l|--lang) SETUP_LANG="$2" ;;
    esac
done

# Interactive language selector if not passed via CLI
if [ -z "$SETUP_LANG" ]; then
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${CYAN}${BOLD}║  🌐 Select Language / Выберите язык:                                     ║${RESET}"
    echo -e "${CYAN}${BOLD}║     [1] English (default)                                                ║${RESET}"
    echo -e "${CYAN}${BOLD}║     [2] Русский                                                          ║${RESET}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════════════════════════╝${RESET}"
    read -p "Choice / Выбор [1]: " -r LANG_INPUT
    if [[ "$LANG_INPUT" == "2" || "$LANG_INPUT" == "ru"* || "$LANG_INPUT" == "RU"* || "$LANG_INPUT" == "рус"* ]]; then
        SETUP_LANG="ru"
    else
        SETUP_LANG="en"
    fi
fi

msg() {
    local en="$1"
    local ru="$2"
    if [ "$SETUP_LANG" == "ru" ]; then
        echo -e "$ru"
    else
        echo -e "$en"
    fi
}

echo -e "${CYAN}${BOLD}======================================================================${RESET}"
if [ "$SETUP_LANG" == "ru" ]; then
    echo -e "${CYAN}${BOLD}         🚀 GRAVIGRAM - АВТОМАТИЧЕСКАЯ УСТАНОВКА ПОД КЛЮЧ             ${RESET}"
else
    echo -e "${CYAN}${BOLD}         🚀 GRAVIGRAM - AUTOMATED ALL-IN-ONE INSTALLER                ${RESET}"
fi
echo -e "${CYAN}${BOLD}======================================================================${RESET}"

# Function to run with sudo if needed
run_sudo() {
    if [ "$EUID" -eq 0 ]; then
        "$@"
    elif command -v sudo &> /dev/null; then
        sudo "$@"
    else
        msg "${RED}❌ Root privileges or sudo utility required to install system packages.${RESET}" \
            "${RED}❌ Требуются права root или утилита sudo для установки системных пакетов.${RESET}"
        exit 1
    fi
}

# 1. Detect distro and package manager
install_system_packages() {
    msg "${YELLOW}[*] Checking and installing system dependencies (Python, pip, venv, curl, tar, ffmpeg)...${RESET}" \
        "${YELLOW}[*] Проверка и установка системных зависимостей (Python, pip, venv, curl, tar, ffmpeg)...${RESET}"
    
    if command -v apt-get &> /dev/null; then
        msg "${CYAN}--> Detected Debian/Ubuntu (apt-get)...${RESET}" \
            "${CYAN}--> Обнаружен Debian/Ubuntu (apt-get)...${RESET}"
        run_sudo apt-get update -qq
        run_sudo apt-get install -y -qq python3 python3-pip python3-venv python3-full curl git tar ffmpeg
    elif command -v dnf &> /dev/null; then
        msg "${CYAN}--> Detected Fedora/RHEL (dnf)...${RESET}" \
            "${CYAN}--> Обнаружен Fedora/RHEL (dnf)...${RESET}"
        run_sudo dnf install -y python3 python3-pip git curl tar ffmpeg
    elif command -v yum &> /dev/null; then
        msg "${CYAN}--> Detected CentOS/RHEL (yum)...${RESET}" \
            "${CYAN}--> Обнаружен CentOS/RHEL (yum)...${RESET}"
        run_sudo yum install -y python3 python3-pip git curl tar ffmpeg
    elif command -v pacman &> /dev/null; then
        msg "${CYAN}--> Detected Arch Linux (pacman)...${RESET}" \
            "${CYAN}--> Обнаружен Arch Linux (pacman)...${RESET}"
        run_sudo pacman -Sy --noconfirm python python-pip git curl tar ffmpeg
    elif command -v apk &> /dev/null; then
        msg "${CYAN}--> Detected Alpine Linux (apk)...${RESET}" \
            "${CYAN}--> Обнаружен Alpine Linux (apk)...${RESET}"
        run_sudo apk add --no-cache python3 py3-pip git curl tar ffmpeg
    elif [ "$(uname)" == "Darwin" ]; then
        msg "${CYAN}--> Detected macOS...${RESET}" \
            "${CYAN}--> Обнаружен macOS...${RESET}"
        if ! command -v brew &> /dev/null; then
            msg "${YELLOW}Homebrew not found. Installing Homebrew...${RESET}" \
                "${YELLOW}Homebrew не найден. Устанавливаем Homebrew...${RESET}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python@3.11 git curl ffmpeg
    else
        msg "${YELLOW}⚠️ Unknown package manager. Assuming Python and tools are installed.${RESET}" \
            "${YELLOW}⚠️ Неизвестный пакетный менеджер. Предполагается, что Python и системные утилиты уже установлены.${RESET}"
    fi
    msg "${GREEN}✔ System dependencies are ready.${RESET}" \
        "${GREEN}✔ Системные зависимости готовы.${RESET}"
}

# 0. Check and clone repo if run from outside
REPO_URL="${1:-https://github.com/kobaltgit/gravigram.git}"
TARGET_DIR="${2:-gravigram}"

if [ ! -f "run.py" ] || [ ! -f "requirements.txt" ]; then
    msg "${YELLOW}[*] Script is running outside an existing project directory.${RESET}" \
        "${YELLOW}[*] Скрипт запущен вне существующего каталога проекта.${RESET}"
    if [ -z "$REPO_URL" ]; then
        if [ "$SETUP_LANG" == "ru" ]; then
            echo -e "${CYAN}Для автоматической установки под ключ укажите адрес Git-репозитория.${RESET}"
            read -p "Введите Git URL (например, https://github.com/kobaltgit/gravigram.git): " -r REPO_URL
        else
            echo -e "${CYAN}For all-in-one setup, specify Git repository URL.${RESET}"
            read -p "Enter Git URL (e.g. https://github.com/kobaltgit/gravigram.git): " -r REPO_URL
        fi
    fi

    if [ -n "$REPO_URL" ]; then
        if ! command -v git &> /dev/null; then
            msg "${YELLOW}[*] Git not found. Installing git and system packages...${RESET}" \
                "${YELLOW}[*] Утилита git не найдена. Установка git и системных пакетов...${RESET}"
            install_system_packages
        fi
        msg "${YELLOW}[*] Cloning repository from ${REPO_URL} into ${TARGET_DIR}...${RESET}" \
            "${YELLOW}[*] Клонирование репозитория из ${REPO_URL} в ${TARGET_DIR}...${RESET}"
        git clone "$REPO_URL" "$TARGET_DIR"
        cd "$TARGET_DIR"
        SCRIPT_DIR="$(pwd)"
        msg "${GREEN}✔ Repository cloned successfully into ${SCRIPT_DIR}.${RESET}" \
            "${GREEN}✔ Репозиторий успешно склонирован в ${SCRIPT_DIR}.${RESET}"
    else
        msg "${RED}❌ Repository URL not specified. Run inside project directory or pass URL as argument.${RESET}" \
            "${RED}❌ Адрес репозитория не указан. Запустите скрипт внутри папки проекта или передайте URL аргументом.${RESET}"
        exit 1
    fi
fi

# Check system tools
if ! command -v python3 &> /dev/null || ! command -v curl &> /dev/null || ! command -v tar &> /dev/null; then
    install_system_packages
else
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
        msg "${YELLOW}Python version ($PY_VER) is below required 3.10. Updating...${RESET}" \
            "${YELLOW}Версия Python ($PY_VER) ниже требуемой 3.10. Обновляем...${RESET}"
        install_system_packages
    fi
fi

# 2. Virtual Environment
if [ ! -d "venv" ]; then
    msg "${YELLOW}[*] Creating Python virtual environment (venv)...${RESET}" \
        "${YELLOW}[*] Создание виртуального окружения (venv)...${RESET}"
    if ! python3 -m venv venv 2>/dev/null; then
        msg "${YELLOW}python3-venv missing. Installing...${RESET}" \
            "${YELLOW}Модуль python3-venv отсутствует. Доустанавливаем...${RESET}"
        install_system_packages
        python3 -m venv venv
    fi
    msg "${GREEN}✔ Python virtual environment (venv) created.${RESET}" \
        "${GREEN}✔ Виртуальное окружение venv создано.${RESET}"
fi

# 3. Python dependencies
msg "${YELLOW}[*] Installing Python dependencies from requirements.txt...${RESET}" \
    "${YELLOW}[*] Установка зависимостей Python из requirements.txt...${RESET}"
./venv/bin/pip install --upgrade pip --quiet
./venv/bin/pip install -r requirements.txt --quiet
msg "${GREEN}✔ Python dependencies installed successfully.${RESET}" \
    "${GREEN}✔ Библиотеки Python успешно установлены.${RESET}"

# 4. Unpack Flutter Mini App
WEB_DIR="$SCRIPT_DIR/frontend_flutter/build/web"
TAR_FILE="$SCRIPT_DIR/miniapp_web.tar.gz"

if [ ! -f "$WEB_DIR/index.html" ]; then
    if [ -f "$SCRIPT_DIR/frontend_flutter/build/index.html" ]; then
        mkdir -p "$WEB_DIR"
        find "$SCRIPT_DIR/frontend_flutter/build" -maxdepth 1 -not -name "build" -not -name "web" -exec mv {} "$WEB_DIR/" \; 2>/dev/null || true
    elif [ -f "$TAR_FILE" ]; then
        msg "${YELLOW}[*] Unpacking Telegram Mini App pre-built web bundle...${RESET}" \
            "${YELLOW}[*] Распаковка готового веб-бандла Telegram Mini App...${RESET}"
        mkdir -p "$WEB_DIR"
        if tar -tzf "$TAR_FILE" 2>/dev/null | grep -q "^web/"; then
            tar -xzf "$TAR_FILE" -C "$SCRIPT_DIR/frontend_flutter/build"
        else
            tar -xzf "$TAR_FILE" -C "$WEB_DIR"
        fi
        msg "${GREEN}✔ Telegram Mini App web bundle is ready.${RESET}" \
            "${GREEN}✔ Веб-приложение Mini App готово к работе.${RESET}"
    fi
fi

# 5. Check and install Antigravity CLI (agy)
if ! command -v agy &> /dev/null && [ ! -f "$HOME/.local/bin/agy" ] && [ ! -f "$HOME/.agy/bin/agy" ] && [ ! -f "/usr/local/bin/agy" ]; then
    msg "${YELLOW}[*] Antigravity CLI (agy) not found. Running official installer...${RESET}" \
        "${YELLOW}[*] Antigravity CLI (agy) не найден. Запуск официального установщика...${RESET}"
    if curl -fsSL https://antigravity.google/cli/install.sh | bash; then
        msg "${GREEN}✔ Antigravity CLI (agy) installed successfully!${RESET}" \
            "${GREEN}✔ Antigravity CLI (agy) успешно установлен!${RESET}"
        export PATH="$HOME/.local/bin:$HOME/.agy/bin:$PATH"
    else
        msg "${YELLOW}⚠️ Failed to automatically download agy. You can install it manually later.${RESET}" \
            "${YELLOW}⚠️ Не удалось автоматически загрузить agy. Вы сможете установить его позже вручную.${RESET}"
    fi
fi

# 6. Launch setup wizard
echo ""
./venv/bin/python setup.py --lang "$SETUP_LANG"

# 7. Optional systemd service
if [ "$(uname)" == "Linux" ] && [ -d "/etc/systemd/system" ]; then
    SERVICE_TEMPLATE="$SCRIPT_DIR/deploy/gravigram.service"
    if [ -f "$SERVICE_TEMPLATE" ]; then
        echo ""
        if [ "$SETUP_LANG" == "ru" ]; then
            read -p "Включить и запустить службу gravigram в systemd для автозапуска 24/7? [Y/n]: " -r ENABLE_SERVICE
        else
            read -p "Enable and start gravigram systemd service for 24/7 auto-start? [Y/n]: " -r ENABLE_SERVICE
        fi
        ENABLE_SERVICE=${ENABLE_SERVICE:-Y}
        if [[ $ENABLE_SERVICE =~ ^[YyДд]$ ]]; then
            msg "${YELLOW}[*] Registering gravigram systemd service...${RESET}" \
                "${YELLOW}[*] Регистрация службы gravigram в systemd...${RESET}"
            CURRENT_USER=$(id -u -n)
            TARGET_SERVICE="/etc/systemd/system/gravigram.service"
            sed -e "s|WorkingDirectory=/opt/gravigram|WorkingDirectory=$SCRIPT_DIR|g" \
                -e "s|ExecStart=/opt/gravigram/venv/bin/python|ExecStart=$SCRIPT_DIR/venv/bin/python|g" \
                -e "s|User=root|User=$CURRENT_USER|g" \
                "$SERVICE_TEMPLATE" | run_sudo tee "$TARGET_SERVICE" > /dev/null
            run_sudo systemctl daemon-reload
            run_sudo systemctl enable --now gravigram
            msg "${GREEN}✔ gravigram service successfully registered and started!${RESET}" \
                "${GREEN}✔ Служба gravigram успешно зарегистрирована и запущена!${RESET}"
            msg "Check status: ${CYAN}sudo systemctl status gravigram${RESET}" \
                "Проверить статус: ${CYAN}sudo systemctl status gravigram${RESET}"
            msg "View logs:    ${CYAN}sudo journalctl -u gravigram -f${RESET}" \
                "Просмотр логов:   ${CYAN}sudo journalctl -u gravigram -f${RESET}"
        fi
    fi
fi
