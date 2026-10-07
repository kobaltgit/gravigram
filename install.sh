#!/usr/bin/env bash
# =============================================================================
# Gravigram - Полный Автономный Установщик (Zero-to-Hero)
# Автоматически устанавливает: Python 3.10+, pip, venv, curl, git, tar,
# настраивает окружение, распаковывает веб-приложение и запускает мастер.
# =============================================================================

set -e

# Цвета для терминала
CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}======================================================================${RESET}"
echo -e "${CYAN}${BOLD}         🚀 GRAVIGRAM - АВТОМАТИЧЕСКАЯ УСТАНОВКА ПОД КЛЮЧ             ${RESET}"
echo -e "${CYAN}${BOLD}======================================================================${RESET}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Функция выполнения с sudo при необходимости
run_sudo() {
    if [ "$EUID" -eq 0 ]; then
        "$@"
    elif command -v sudo &> /dev/null; then
        sudo "$@"
    else
        echo -e "${RED}❌ Требуются права root или утилита sudo для установки системных пакетов.${RESET}"
        exit 1
    fi
}

# 1. Определение дистрибутива и пакетного менеджера
install_system_packages() {
    echo -e "${YELLOW}[*] Проверка и установка системных зависимостей (Python, pip, venv, curl, tar, ffmpeg)...${RESET}"
    
    if command -v apt-get &> /dev/null; then
        echo -e "${CYAN}--> Обнаружен Debian/Ubuntu (apt-get)...${RESET}"
        run_sudo apt-get update -qq
        run_sudo apt-get install -y -qq python3 python3-pip python3-venv python3-full curl git tar ffmpeg
    elif command -v dnf &> /dev/null; then
        echo -e "${CYAN}--> Обнаружен Fedora/RHEL (dnf)...${RESET}"
        run_sudo dnf install -y python3 python3-pip git curl tar ffmpeg
    elif command -v yum &> /dev/null; then
        echo -e "${CYAN}--> Обнаружен CentOS/RHEL (yum)...${RESET}"
        run_sudo yum install -y python3 python3-pip git curl tar ffmpeg
    elif command -v pacman &> /dev/null; then
        echo -e "${CYAN}--> Обнаружен Arch Linux (pacman)...${RESET}"
        run_sudo pacman -Sy --noconfirm python python-pip git curl tar ffmpeg
    elif command -v apk &> /dev/null; then
        echo -e "${CYAN}--> Обнаружен Alpine Linux (apk)...${RESET}"
        run_sudo apk add --no-cache python3 py3-pip git curl tar ffmpeg
    elif [ "$(uname)" == "Darwin" ]; then
        echo -e "${CYAN}--> Обнаружен macOS...${RESET}"
        if ! command -v brew &> /dev/null; then
            echo -e "${YELLOW}Homebrew не найден. Устанавливаем Homebrew...${RESET}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python@3.11 git curl ffmpeg
    else
        echo -e "${YELLOW}⚠️ Неизвестный пакетный менеджер. Предполагается, что Python и системные утилиты уже установлены.${RESET}"
    fi
    echo -e "${GREEN}✔ Системные зависимости готовы.${RESET}"
}

# 0. Проверка и автоматическое клонирование репозитория, если скрипт запущен вне каталога проекта
REPO_URL="${1:-https://github.com/kobaltgit/gravigram.git}"
TARGET_DIR="${2:-gravigram}"

if [ ! -f "run.py" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}[*] Скрипт запущен вне существующего каталога проекта.${RESET}"
    if [ -z "$REPO_URL" ]; then
        echo -e "${CYAN}Для автоматической установки под ключ укажите адрес Git-репозитория.${RESET}"
        read -p "Введите Git URL (например, https://github.com/username/antigravity_bot.git): " -r REPO_URL
    fi

    if [ -n "$REPO_URL" ]; then
        if ! command -v git &> /dev/null; then
            echo -e "${YELLOW}[*] Утилита git не найдена. Установка git и системных пакетов...${RESET}"
            install_system_packages
        fi
        echo -e "${YELLOW}[*] Клонирование репозитория из ${REPO_URL} в ${TARGET_DIR}...${RESET}"
        git clone "$REPO_URL" "$TARGET_DIR"
        cd "$TARGET_DIR"
        SCRIPT_DIR="$(pwd)"
        echo -e "${GREEN}✔ Репозиторий успешно склонирован в ${SCRIPT_DIR}.${RESET}"
    else
        echo -e "${RED}❌ Адрес репозитория не указан. Запустите скрипт внутри папки проекта или передайте URL аргументом.${RESET}"
        exit 1
    fi
fi

# Проверяем, нужен ли системный инсталл
if ! command -v python3 &> /dev/null || ! command -v curl &> /dev/null || ! command -v tar &> /dev/null; then
    install_system_packages
else
    # Проверяем версию Python
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
        echo -e "${YELLOW}Версия Python ($PY_VER) ниже требуемой 3.10. Обновляем...${RESET}"
        install_system_packages
    fi
fi

# 2. Создание виртуального окружения Python
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[*] Создание виртуального окружения (venv)...${RESET}"
    if ! python3 -m venv venv 2>/dev/null; then
        echo -e "${YELLOW}Модуль python3-venv отсутствует. Доустанавливаем...${RESET}"
        install_system_packages
        python3 -m venv venv
    fi
    echo -e "${GREEN}✔ Виртуальное окружение venv создано.${RESET}"
fi

# 3. Установка Python-зависимостей проекта
echo -e "${YELLOW}[*] Установка зависимостей Python из requirements.txt...${RESET}"
./venv/bin/pip install --upgrade pip --quiet
./venv/bin/pip install -r requirements.txt --quiet
echo -e "${GREEN}✔ Библиотеки Python успешно установлены.${RESET}"

# 4. Распаковка собранного Flutter Mini App (если сборка ещё не распакована)
WEB_DIR="$SCRIPT_DIR/frontend_flutter/build/web"
TAR_FILE="$SCRIPT_DIR/miniapp_web.tar.gz"

if [ ! -f "$WEB_DIR/index.html" ]; then
    if [ -f "$SCRIPT_DIR/frontend_flutter/build/index.html" ]; then
        mkdir -p "$WEB_DIR"
        find "$SCRIPT_DIR/frontend_flutter/build" -maxdepth 1 -not -name "build" -not -name "web" -exec mv {} "$WEB_DIR/" \; 2>/dev/null || true
    elif [ -f "$TAR_FILE" ]; then
        echo -e "${YELLOW}[*] Распаковка готового веб-бандла Telegram Mini App...${RESET}"
        mkdir -p "$WEB_DIR"
        if tar -tzf "$TAR_FILE" 2>/dev/null | grep -q "^web/"; then
            tar -xzf "$TAR_FILE" -C "$SCRIPT_DIR/frontend_flutter/build"
        else
            tar -xzf "$TAR_FILE" -C "$WEB_DIR"
        fi
        echo -e "${GREEN}✔ Веб-приложение Mini App готово к работе.${RESET}"
    fi
fi

# 5. Проверка и автоматическая установка Antigravity CLI (agy)
if ! command -v agy &> /dev/null && [ ! -f "$HOME/.local/bin/agy" ] && [ ! -f "$HOME/.agy/bin/agy" ] && [ ! -f "/usr/local/bin/agy" ]; then
    echo -e "${YELLOW}[*] Antigravity CLI (agy) не найден. Запуск официального установщика...${RESET}"
    if curl -fsSL https://antigravity.google/cli/install.sh | bash; then
        echo -e "${GREEN}✔ Antigravity CLI (agy) успешно установлен!${RESET}"
        export PATH="$HOME/.local/bin:$HOME/.agy/bin:$PATH"
    else
        echo -e "${YELLOW}⚠️ Не удалось автоматически загрузить agy. Вы сможете установить его позже вручную.${RESET}"
    fi
fi

# 6. Запуск интерактивного мастера настройки (.env, БД, токены)
echo ""
./venv/bin/python setup.py

# 7. Опциональный автозапуск службы systemd на Linux
if [ "$(uname)" == "Linux" ] && [ -d "/etc/systemd/system" ]; then
    SERVICE_TEMPLATE="$SCRIPT_DIR/deploy/gravigram.service"
    if [ -f "$SERVICE_TEMPLATE" ]; then
        echo ""
        read -p "Включить и запустить службу gravigram в systemd для автозапуска 24/7? [Y/n]: " -r ENABLE_SERVICE
        ENABLE_SERVICE=${ENABLE_SERVICE:-Y}
        if [[ $ENABLE_SERVICE =~ ^[YyДд]$ ]]; then
            echo -e "${YELLOW}[*] Регистрация службы gravigram в systemd...${RESET}"
            CURRENT_USER=$(id -u -n)
            TARGET_SERVICE="/etc/systemd/system/gravigram.service"
            # Настраиваем актуальные пути и пользователя
            sed -e "s|WorkingDirectory=/opt/gravigram|WorkingDirectory=$SCRIPT_DIR|g" \
                -e "s|ExecStart=/opt/gravigram/venv/bin/python|ExecStart=$SCRIPT_DIR/venv/bin/python|g" \
                -e "s|User=root|User=$CURRENT_USER|g" \
                "$SERVICE_TEMPLATE" | run_sudo tee "$TARGET_SERVICE" > /dev/null
            run_sudo systemctl daemon-reload
            run_sudo systemctl enable --now gravigram
            echo -e "${GREEN}✔ Служба gravigram успешно зарегистрирована и запущена!${RESET}"
            echo -e "Проверить статус: ${CYAN}sudo systemctl status gravigram${RESET}"
            echo -e "Просмотр логов:   ${CYAN}sudo journalctl -u gravigram -f${RESET}"
        fi
    fi
fi
