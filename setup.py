#!/usr/bin/env python3
"""
Интерактивный мастер установки и настройки Antigravity Hub (All-in-One).
Работает на Windows, Linux и macOS. Не требует внешних зависимостей для базового запуска.
"""

import os
import sys
import re
import shutil
import tarfile
import socket
import tempfile
import platform
import subprocess
from pathlib import Path

# ANSI colors for pleasant CLI experience
class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

def supports_color():
    return sys.stdout.isatty() and (platform.system() != "Windows" or "WT_SESSION" in os.environ or "TERM" in os.environ or os.environ.get("ANSICON"))

def c(text, color_code):
    return f"{color_code}{text}{Colors.RESET}" if supports_color() else text

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════════════════╗
║              🚀 ANTIGRAVITY HUB - ИНТЕРАКТИВНЫЙ УСТАНОВЩИК              ║
║         (Telegram Bot + Flutter Web Mini App + Antigravity Engine)       ║
╚══════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
""" if supports_color() else """
============================================================================
              ANTIGRAVITY HUB - ИНТЕРАКТИВНЫЙ УСТАНОВЩИК
         (Telegram Bot + Flutter Web Mini App + Antigravity Engine)
============================================================================
"""
    print(banner)

def load_existing_env(env_path: Path) -> dict:
    env_data = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_data[k.strip()] = v.strip().strip("'\"")
    return env_data

def prompt_user(prompt_text: str, default_val: str = "", validator=None, secret: bool = False) -> str:
    default_hint = f" [{c(default_val, Colors.DIM)}]" if default_val else ""
    full_prompt = f"{c('?', Colors.CYAN)} {prompt_text}{default_hint}: "
    
    while True:
        try:
            val = input(full_prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n" + c("Установка прервана пользователем.", Colors.YELLOW))
            sys.exit(0)

        if not val and default_val:
            val = default_val

        if validator:
            valid, msg = validator(val)
            if not valid:
                print(f"  {c('✖', Colors.RED)} {msg}")
                continue

        return val

def validate_bot_token(token: str):
    token = token.strip()
    if not token:
        return False, "Токен не может быть пустым."
    if token.startswith("1234567890:ABC"):
        return False, "Укажите настоящий токен от @BotFather, а не шаблон."
    if not re.match(r"^\d+:[A-Za-z0-9_-]+$", token):
        return False, "Неверный формат токена Telegram бота (должен быть вида 1234567890:ABC...)."
    return True, ""

def validate_admin_id(admin_id_str: str):
    admin_id_str = admin_id_str.strip()
    if not admin_id_str.isdigit() or int(admin_id_str) <= 0:
        return False, "Admin ID должен быть положительным числом (узнайте в @userinfobot)."
    return True, ""

def validate_port(port_str: str):
    port_str = port_str.strip()
    if not port_str.isdigit() or not (1 <= int(port_str) <= 65535):
        return False, "Порт должен быть числом от 1 до 65535."
    return True, ""

def run_cmd(cmd_list: list) -> tuple:
    """Executes a system command and returns (returncode, stdout)."""
    try:
        proc = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return proc.returncode, proc.stdout
    except Exception as e:
        return 1, str(e)

def run_nginx_certbot_setup(domain: str, port: int, email: str = "") -> bool:
    """Installs Nginx, creates reverse proxy config, and issues Let's Encrypt certificate on Linux."""
    if platform.system().lower() != "linux":
        print(c("⚠️ Автоматическая настройка Nginx и Certbot поддерживается только на Linux серверах.", Colors.YELLOW))
        return False

    is_root = (os.geteuid() == 0) if hasattr(os, "geteuid") else False
    sudo_pfx = [] if is_root else ["sudo"]

    # 1. Detect package manager and install nginx, certbot
    pkg_mgr = None
    for pm in ["apt-get", "dnf", "yum", "pacman", "apk"]:
        if shutil.which(pm):
            pkg_mgr = pm
            break

    if not pkg_mgr:
        print(c("❌ Не удалось определить системный пакетный менеджер (apt, dnf, pacman).", Colors.RED))
        return False

    print(f"[*] Установка Nginx и Certbot через {pkg_mgr}...")
    if pkg_mgr == "apt-get":
        run_cmd(sudo_pfx + ["apt-get", "update", "-y"])
        rc, out = run_cmd(sudo_pfx + ["apt-get", "install", "-y", "nginx", "certbot", "python3-certbot-nginx"])
    elif pkg_mgr in ["dnf", "yum"]:
        rc, out = run_cmd(sudo_pfx + [pkg_mgr, "install", "-y", "nginx", "certbot", "python3-certbot-nginx"])
    elif pkg_mgr == "pacman":
        rc, out = run_cmd(sudo_pfx + ["pacman", "-Sy", "--noconfirm", "nginx", "certbot", "certbot-nginx"])
    elif pkg_mgr == "apk":
        rc, out = run_cmd(sudo_pfx + ["apk", "add", "--no-cache", "nginx", "certbot", "certbot-nginx"])
    else:
        rc, out = 1, "Unsupported"

    if rc != 0:
        print(c(f"⚠️ Ошибка установки пакетов Nginx/Certbot:\n{out[:400]}", Colors.YELLOW))
        return False

    # 2. Write Nginx Reverse Proxy Config
    nginx_conf = f"""# Antigravity Hub Nginx Reverse Proxy
server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    sites_available = Path("/etc/nginx/sites-available")
    sites_enabled = Path("/etc/nginx/sites-enabled")
    conf_d = Path("/etc/nginx/conf.d")

    try:
        tmp_conf = Path(tempfile.gettempdir()) / "antigravity.conf"
        tmp_conf.write_text(nginx_conf, encoding="utf-8")

        if sites_available.exists():
            conf_target = sites_available / "antigravity.conf"
            run_cmd(sudo_pfx + ["cp", str(tmp_conf), str(conf_target)])
            if sites_enabled.exists():
                symlink = sites_enabled / "antigravity.conf"
                run_cmd(sudo_pfx + ["ln", "-sf", str(conf_target), str(symlink)])
                # Remove default placeholder site if present
                def_site = sites_enabled / "default"
                if def_site.exists():
                    run_cmd(sudo_pfx + ["rm", "-f", str(def_site)])
        elif conf_d.exists():
            conf_target = conf_d / "antigravity.conf"
            run_cmd(sudo_pfx + ["cp", str(tmp_conf), str(conf_target)])
    except Exception as e:
        print(c(f"⚠️ Не удалось записать конфигурацию Nginx: {e}", Colors.YELLOW))
        return False

    # 3. Test and restart Nginx
    run_cmd(sudo_pfx + ["nginx", "-t"])
    run_cmd(sudo_pfx + ["systemctl", "enable", "nginx"])
    run_cmd(sudo_pfx + ["systemctl", "restart", "nginx"])

    # 4. Open firewall ports if ufw or firewalld are present
    if shutil.which("ufw"):
        run_cmd(sudo_pfx + ["ufw", "allow", "80/tcp"])
        run_cmd(sudo_pfx + ["ufw", "allow", "443/tcp"])
    elif shutil.which("firewall-cmd"):
        run_cmd(sudo_pfx + ["firewall-cmd", "--add-service=http", "--add-service=https", "--permanent"])
        run_cmd(sudo_pfx + ["firewall-cmd", "--reload"])

    # 5. Issue Let's Encrypt SSL Certificate
    print(f"[*] Запуск Certbot для получения SSL-сертификата {domain}...")
    certbot_cmd = sudo_pfx + [
        "certbot", "--nginx", "-d", domain, "--non-interactive", "--agree-tos", "--redirect"
    ]
    if email.strip():
        certbot_cmd.extend(["-m", email.strip()])
    else:
        certbot_cmd.append("--register-unsafely-without-email")

    rc, out = run_cmd(certbot_cmd)
    if rc == 0:
        print(c("  ✔ SSL-сертификат Let's Encrypt успешно получен и настроен в Nginx!", Colors.GREEN))
        run_cmd(sudo_pfx + ["systemctl", "reload", "nginx"])
        return True
    else:
        print(c(f"  ⚠️ Certbot сообщил о проблеме при выпуске SSL:\n{out[:500]}", Colors.YELLOW))
        return False

def configure_ssl_and_domain(port: int, current_url: str = "") -> str:
    """Configures domain, Nginx reverse proxy, and Let's Encrypt SSL certificate."""
    print("\n" + c("--- [ Настройка доступа к Telegram Mini App (HTTPS / SSL) ] ---", Colors.BOLD))
    print("ℹ️  По правилам Telegram, Mini App на смартфонах и ПК открывается ТОЛЬКО по доверенному HTTPS (HTTP блокируется).")
    print("   1 - Автоматически настроить Nginx + бесплатный SSL Let's Encrypt (у меня есть домен) [Для VPS]")
    print("   2 - Ввести готовый HTTPS URL вручную (Nginx Proxy Manager, Cloudflare, Traefik, SSH-туннель)")
    print("   3 - Пропустить настройку Mini App (только чат-бот, без кнопки приложения в Telegram)")

    default_choice = "2" if current_url else ("1" if platform.system().lower() == "linux" else "3")
    choice = prompt_user("Выберите вариант", default_val=default_choice)

    if choice == "3":
        print(c("  ✔ Настройка Mini App пропущена. Бот будет полноценно работать через чат (текст, голос, файлы, задачи).", Colors.YELLOW))
        return ""

    if choice == "2":
        return prompt_user(
            "Введите готовый публичный HTTPS URL (например https://bot.example.com)",
            default_val=current_url
        )

    if choice == "1":
        if platform.system().lower() != "linux":
            print(c("⚠️ Автоматическая настройка Nginx+Certbot доступна на Linux серверах.", Colors.YELLOW))
            manual = prompt_user("Введите готовый HTTPS URL или Enter для пропуска", default_val=current_url)
            return manual

        domain = prompt_user("Введите ваш домен (например bot.mydomain.ru или agy.example.com)")
        domain = domain.strip().replace("https://", "").replace("http://", "").strip("/")
        if not domain:
            print(c("  Домен не указан, пропуск настройки SSL.", Colors.YELLOW))
            return ""

        # Validate DNS resolution
        try:
            resolved_ip = socket.gethostbyname(domain)
            print(c(f"  ✔ DNS домена {domain} успешно разрешён: {resolved_ip}", Colors.GREEN))
        except Exception as e:
            print(c(f"  ⚠️ Предупреждение: Домен {domain} пока не отвечает в DNS ({e}).", Colors.YELLOW))
            proceed = prompt_user("Всё равно продолжить настройку Nginx и выпуск SSL? [y/N]", default_val="n")
            if proceed.lower() not in ["y", "yes", "да"]:
                return f"https://{domain}"

        email = prompt_user("Email для уведомлений Let's Encrypt (Enter для пропуска)", default_val="")

        success = run_nginx_certbot_setup(domain, port, email)
        if success:
            https_url = f"https://{domain}"
            print(c(f"  🎉 Успешно! Telegram Mini App будет доступен по адресу: {https_url}", Colors.GREEN))
            return https_url
        else:
            print(c(f"  ⚠️ SSL не был выпущен автоматически. Домен сохранён как https://{domain}", Colors.YELLOW))
            return f"https://{domain}"

    return current_url

def find_agy_binary():
    exe = shutil.which("agy") or shutil.which("agy.exe")
    if exe:
        return exe
    home = Path.home()
    candidates = [
        home / ".local" / "bin" / "agy",
        home / ".agy" / "bin" / "agy",
        Path("/usr/local/bin/agy"),
        Path("/usr/bin/agy"),
    ]
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        candidates.append(Path(local_app_data) / "agy" / "bin" / "agy.exe")

    for cand in candidates:
        if cand.exists():
            return str(cand)
    return None

def check_agy_auth(agy_exe: str) -> bool:
    """Checks if Antigravity CLI is authenticated by calling agy models."""
    try:
        proc = subprocess.run([agy_exe, "models"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=12)
        return proc.returncode == 0 and "gemini" in proc.stdout.lower()
    except Exception:
        return False

def interactive_agy_auth(agy_exe: str) -> bool:
    """Runs interactive Antigravity turn to perform device OAuth login with stdin/stdout attached."""
    print("\n" + c("==============================================================", Colors.CYAN))
    print(c("🔐 АВТОРИЗАЦИЯ GOOGLE ANTIGRAVITY", Colors.BOLD))
    print("1. Перейдите по ссылке, которая появится ниже (в браузере).")
    print("2. Авторизуйтесь в Google аккаунте и скопируйте ответный код авторизации.")
    print("3. Вставьте код в терминал и нажмите Enter.")
    print(c("==============================================================\n", Colors.CYAN))
    try:
        subprocess.run([agy_exe, "-p", "Привет"], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        if check_agy_auth(agy_exe):
            print(c("  ✔ Авторизация Antigravity успешно подтверждена!", Colors.GREEN))
            return True
        else:
            print(c("  ⚠️ Не удалось подтвердить авторизацию. Вы сможете выполнить её позже командой /login в Telegram-боте.", Colors.YELLOW))
            return False
    except Exception as e:
        print(c(f"  ✖ Ошибка при авторизации agy: {e}", Colors.RED))
        return False

def main():
    print_banner()

    root_dir = Path(__file__).resolve().parent
    env_path = root_dir / ".env"
    existing_env = load_existing_env(env_path)

    # 1. Проверка версии Python
    py_ver = sys.version_info
    print(f"[*] Проверка окружения Python: {py_ver.major}.{py_ver.minor}.{py_ver.micro} ({platform.system()} {platform.machine()})")
    if py_ver < (3, 10):
        print(c(f"❌ Ошибка: Требуется Python 3.10 или выше (у вас {py_ver.major}.{py_ver.minor}).", Colors.RED))
        sys.exit(1)
    print(c("  ✔ Python совместим.", Colors.GREEN))

    # 2. Интерактивный диалог настройки
    print("\n" + c("--- [ Шаг 1: Настройка доступа Telegram и Сервера ] ---", Colors.BOLD))

    # Token
    current_token = existing_env.get("TELEGRAM_BOT_TOKEN", "")
    bot_token = prompt_user(
        "Введите Telegram Bot Token (получите у @BotFather)",
        default_val=current_token,
        validator=validate_bot_token
    )

    # Admin ID
    current_admin = existing_env.get("TELEGRAM_ADMIN_ID", "")
    admin_id = prompt_user(
        "Введите ваш цифровой Telegram ID (узнайте у @userinfobot)",
        default_val=current_admin,
        validator=validate_admin_id
    )

    # Port
    current_port = existing_env.get("PORT", "8000")
    port = prompt_user(
        "Порт для веб-сервера и Mini App",
        default_val=current_port,
        validator=validate_port
    )

    # WebApp URL / Domain / SSL
    current_url = existing_env.get("WEBAPP_URL", "")
    webapp_url = configure_ssl_and_domain(port=int(port), current_url=current_url)

    # Mode
    current_confirm = existing_env.get("CONFIRM_MODE", "false").lower() == "true"
    confirm_choice = prompt_user(
        "Режим безопасности [1 - Автономный /auto, 2 - С подтверждением команд /confirm]",
        default_val="2" if current_confirm else "1"
    )
    confirm_mode = "true" if confirm_choice == "2" else "false"

    # Default model
    current_model = existing_env.get("DEFAULT_MODEL", "gemini-3.7-flash")
    default_model = prompt_user(
        "Модель по умолчанию",
        default_val=current_model
    )

    # Context hint
    current_hint = existing_env.get("SYSTEM_CONTEXT_HINT", "")
    context_hint = prompt_user(
        "Дополнительное описание хоста/сервера для агента (Enter для автоопределения)",
        default_val=current_hint
    )

    # 3. Сохранение файла .env
    print("\n" + c("--- [ Шаг 2: Генерация конфигурации .env ] ---", Colors.BOLD))
    env_content = f"""# =============================================================================
# Antigravity Hub Configuration
# Generated automatically by setup.py
# =============================================================================

TELEGRAM_BOT_TOKEN={bot_token}
TELEGRAM_ADMIN_ID={admin_id}
WEBAPP_URL={webapp_url}
PORT={port}
HOST=0.0.0.0
CONFIRM_MODE={confirm_mode}
DEFAULT_MODEL={default_model}
SYSTEM_CONTEXT_HINT={context_hint}
DEFAULT_WORKSPACE_PATH={str(root_dir)}
DB_PATH={str(root_dir / "data" / "bot.db")}
"""
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)
    print(c(f"  ✔ Файл конфигурации {env_path.name} успешно сохранён.", Colors.GREEN))

    # 4. Проверка бинарника Antigravity
    print("\n" + c("--- [ Шаг 3: Проверка Antigravity Engine ] ---", Colors.BOLD))
    agy_exe = find_agy_binary()
    if agy_exe:
        print(c(f"  ✔ Antigravity CLI обнаружен: {agy_exe}", Colors.GREEN))
    else:
        print(c("  ⚠️ Antigravity CLI (agy) не найден в стандартных путях системы.", Colors.YELLOW))
        install_agy = prompt_user("Установить официальный Antigravity CLI прямо сейчас? [Y/n]", default_val="Y")
        if install_agy.lower() in ("y", "yes", "д", "да"):
            print("[*] Загрузка и установка Antigravity CLI...")
            try:
                if platform.system() == "Windows":
                    subprocess.run(["powershell", "-Command", "irm https://antigravity.google/cli/install.ps1 | iex"], check=False)
                else:
                    subprocess.run(["bash", "-c", "curl -fsSL https://antigravity.google/cli/install.sh | bash"], check=False)
                agy_exe = find_agy_binary()
                if agy_exe:
                    print(c(f"  ✔ Antigravity CLI успешно установлен: {agy_exe}", Colors.GREEN))
                else:
                    print(c("  ✔ Установщик завершил работу. Если agy не виден, перезапустите терминал.", Colors.GREEN))
            except Exception as e:
                print(c(f"  ✖ Ошибка при установке agy: {e}", Colors.RED))
        else:
            print("  Вы сможете установить его позже или указать точный путь в .env (параметр AGY_BIN_PATH).")

    if agy_exe:
        print("[*] Проверка статуса авторизации Antigravity...")
        if check_agy_auth(agy_exe):
            print(c("  ✔ Antigravity CLI авторизован и готов к работе с Google аккаунтом.", Colors.GREEN))
        else:
            print(c("  ⚠️ Antigravity CLI требует авторизации Google аккаунта.", Colors.YELLOW))
            do_auth = prompt_user("Пройти авторизацию через браузер прямо сейчас? [Y/n]", default_val="Y")
            if do_auth.lower() in ("y", "yes", "д", "да"):
                interactive_agy_auth(agy_exe)
            else:
                print("  Вы сможете авторизоваться позже в консоли или через Telegram-бота командой /login.")

    # 5. Проверка и подготовка Flutter Web сборки
    print("\n" + c("--- [ Шаг 4: Подготовка Flutter Web Mini App ] ---", Colors.BOLD))
    web_dir = root_dir / "frontend_flutter" / "build" / "web"
    web_index = web_dir / "index.html"
    tar_archive = root_dir / "miniapp_web.tar.gz"

    if web_index.exists():
        print(c(f"  ✔ Сборка Flutter Web уже готова ({web_dir}).", Colors.GREEN))
    elif (web_dir.parent / "index.html").exists():
        # Already extracted into build/ root; relocate into build/web/
        web_dir.mkdir(parents=True, exist_ok=True)
        for item in list(web_dir.parent.iterdir()):
            if item.name != "web":
                try:
                    shutil.move(str(item), str(web_dir / item.name))
                except Exception:
                    pass
        print(c(f"  ✔ Сборка Flutter Web перемещена в {web_dir}.", Colors.GREEN))
    elif tar_archive.exists():
        print(f"[*] Распаковка готового архива Mini App ({tar_archive.name})...")
        try:
            web_dir.mkdir(parents=True, exist_ok=True)
            with tarfile.open(tar_archive, "r:gz") as tar:
                members = tar.getmembers()
                has_web_root = any(m.name.startswith("web/") or m.name.startswith("./web/") for m in members)
                extract_target = web_dir.parent if has_web_root else web_dir
                tar.extractall(path=extract_target)

            # If files were extracted into build/ instead of build/web/, move them
            if not web_index.exists() and (web_dir.parent / "index.html").exists():
                for item in list(web_dir.parent.iterdir()):
                    if item.name != "web":
                        try:
                            shutil.move(str(item), str(web_dir / item.name))
                        except Exception:
                            pass

            if web_index.exists():
                print(c("  ✔ Готовый веб-бандл Mini App успешно распакован!", Colors.GREEN))
            else:
                print(c("  ⚠️ Архив распакован, но index.html не найден по стандартному пути.", Colors.YELLOW))
        except Exception as e:
            print(c(f"  ✖ Ошибка распаковки архива: {e}", Colors.RED))
    else:
        flutter_cmd = shutil.which("flutter")
        if flutter_cmd:
            print("[*] Запуск компиляции Flutter Web...")
            subprocess.run([flutter_cmd, "pub", "get"], cwd=root_dir / "frontend_flutter")
            subprocess.run([flutter_cmd, "build", "web", "--release"], cwd=root_dir / "frontend_flutter")
            if web_index.exists():
                print(c("  ✔ Flutter Web скомпилирован успешно!", Colors.GREEN))
        else:
            print(c("  ⚠️ Готовая сборка Flutter Web не найдена. Установите Flutter SDK для компиляции или разархивируйте miniapp_web.tar.gz.", Colors.YELLOW))

    # 6. Инициализация базы данных SQLite
    print("\n" + c("--- [ Шаг 5: Инициализация Базы Данных SQLite ] ---", Colors.BOLD))
    data_dir = root_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Import dynamically using current sys.path
        if str(root_dir) not in sys.path:
            sys.path.insert(0, str(root_dir))
        import asyncio
        from src.database import init_db
        asyncio.run(init_db())
        print(c("  ✔ База данных успешно инициализирована (data/bot.db).", Colors.GREEN))
    except Exception as e:
        print(c(f"  ⚠️ Ошибка первичной инициализации БД: {e}", Colors.YELLOW))
        print("  БД будет автоматически создана при первом запуске run.py.")

    # 7. Генерация systemd службы на Linux (опционально)
    if platform.system() == "Linux":
        print("\n" + c("--- [ Шаг 6: Служба автозапуска Linux (systemd) ] ---", Colors.BOLD))
        deploy_dir = root_dir / "deploy"
        deploy_dir.mkdir(exist_ok=True)
        service_file = deploy_dir / "antigravity-bot.service"
        python_exe = sys.executable

        service_content = f"""[Unit]
Description=Antigravity Universal Bot & Mini App
After=network.target

[Service]
Type=simple
User={os.environ.get('USER', 'root')}
WorkingDirectory={root_dir}
ExecStart={python_exe} run.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
        with open(service_file, "w", encoding="utf-8") as f:
            f.write(service_content)
        print(c(f"  ✔ Создан шаблон службы: {service_file}", Colors.GREEN))
        print(f"  Для регистрации в системе выполните:")
        print(c(f"    sudo cp {service_file} /etc/systemd/system/", Colors.CYAN))
        print(c("    sudo systemctl daemon-reload && sudo systemctl enable --now antigravity-bot", Colors.CYAN))

    # 8. Завершающий баннер
    success_banner = f"""
{Colors.GREEN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════════════════╗
║                   🎉 НАСТРОЙКА УСПЕШНО ЗАВЕРШЕНА!                        ║
╚══════════════════════════════════════════════════════════════════════════╝{Colors.RESET}

Для запуска всего комплекса (Telegram Бот + Web-сервер Mini App) выполните:
  {c('python run.py', Colors.CYAN + Colors.BOLD)}

Веб-приложение доступно локально по адресу:
  {c(f'http://localhost:{port}', Colors.CYAN)}
""" if supports_color() else f"""
============================================================================
                   НАСТРОЙКА УСПЕШНО ЗАВЕРШЕНА!
============================================================================

Для запуска всего комплекса (Telegram Бот + Web-сервер Mini App) выполните:
  python run.py

Веб-приложение доступно локально по адресу:
  http://localhost:{port}
"""
    print(success_banner)

if __name__ == "__main__":
    main()
