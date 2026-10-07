<div align="center">

<img src="icon.svg" width="128" height="128" alt="Gravigram Logo" />

# Gravigram

**Universal Personal AI Agent Control Plane**  
*Bridging Google Antigravity (AGY) with Telegram Bot Streaming & Flutter Mini App*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![aiogram 3](https://img.shields.io/badge/telegram-aiogram_3-2CA5E0.svg)](https://docs.aiogram.dev/)
[![Flutter 3.44+](https://img.shields.io/badge/flutter-3.44+-02569B.svg)](https://flutter.dev/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests: 70 passed](https://img.shields.io/badge/tests-70%20passed-brightgreen.svg)](#-automated-testing)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)

🌐 [English](README.md) | [Русский](README_RU.md)

</div>

> **Gravigram — Universal Personal AI Agent Control Plane**: Bridging **Google Antigravity (AGY)** with a live Telegram streaming bot and a sleek **Flutter Web Telegram Mini App (TMA)** for visual workspace, session, task, and account management.

---

## 📑 Table of Contents

1. [Key Features](#-key-features)
2. [Architecture Overview](#-architecture-overview)
3. [One-Click Installation](#-one-click-installation)
   - [Linux / VPS (Ubuntu, Debian)](#-linux--vps)
   - [Windows (Local PC / Server)](#-windows)
   - [Docker / Container Deployment](#-docker--container-deployment)
4. [Google Antigravity Multi-Account Manager](#-google-antigravity-multi-account-manager)
5. [Telegram Bot Commands & Controls](#-telegram-bot-commands--controls)
6. [Flutter Mini App Interface (TMA)](#-flutter-mini-app-interface-tma)
7. [Scheduled Tasks & Automation Engine](#-scheduled-tasks--automation-engine)
8. [Configuration Guide (.env)](#-configuration-guide-env)
9. [Repository Structure](#-repository-structure)
10. [Automated Testing](#-automated-testing)
11. [Wiki & Documentation Protocol](#-wiki--documentation-protocol)

---

## 🌟 Key Features

* ⚡ **Live Telegram Streaming**: Dynamically updates a single Telegram message during turn generation (`💭 Thinking...` $\to$ `🛠 Tool Execution` $\to$ `📝 Markdown / HTML Response`).
* 💙 **Native Flutter Telegram Mini App (TMA)**: Material 3 SPA running seamlessly in Telegram (Desktop, iOS, Android, Web), providing visual dashboards, file browser, session history, and task scheduler.
* 🔑 **1-Click Multi-Account Switcher**: Switch between linked Google accounts without restarting or re-authenticating. Supports automatic loopback OAuth 2.0 (port 8085), mobile manual codes, and Windows Credential Manager synchronization.
* 🔒 **Strict Single-User Security**: Fail-closed architecture. All endpoints, bot handlers, and Mini App API calls are strictly protected and verified for the designated `TELEGRAM_ADMIN_ID`.
* 🕒 **Autonomous Cron Task Scheduler**: Run agent prompts on schedule (daily time or cron intervals) with automated execution, failure handling, run history logs, and instant preset templates.
* 🎙 **100% Offline Voice Transcription**: Integrated `faster-whisper` engine transcribing voice messages locally on CPU/GPU without external API keys.
* 📄 **File & Document Inspector**: Send scripts, logs, PDFs, and data files (`.py`, `.log`, `.txt`, `.json`, `.csv`, `.pdf`) directly into chat for instant analysis, bugfixing, and code generation.
* 📦 **Artifact Delivery**: Generates and uploads newly created code files, reports, and data files back into Telegram as downloadable documents.
* 🛡 **Human-in-the-Loop Mode**: Switch between `/auto` (full autonomy with `--dangerously-skip-permissions`) and `/confirm` (interactive inline buttons for shell commands and file changes).

---

## 🏗 Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │            Telegram Client           │
                      │   (iOS / Android / Desktop / Web)    │
                      └───────┬──────────────────────┬───────┘
                              │                      │
                  Chat & Voice│                      │Mini App (HTTPS)
                              ▼                      ▼
    ┌──────────────────────────────────┐   ┌──────────────────────────────────┐
    │       aiogram 3 Dispatcher       │   │    Flutter Web TMA (FastSPA)     │
    │   • AuthMiddleware (Admin ID)    │   │   • Material 3 UI                │
    │   • Chat & Voice Handlers        │   │   • Projects & Files Viewer      │
    │   • Multi-Account Manager Menu   │   │   • Tasks & Session Dashboards   │
    └─────────────────┬────────────────┘   └─────────────────┬────────────────┘
                      │                                      │
                      │            ┌─────────────────────────┘
                      ▼            ▼ REST API / WebSocket
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           FastAPI Web Server                            │
    │   • HMAC-SHA256 initData Auth & Trusted Reverse Proxies Verification   │
    │   • REST Endpoints: /api/projects, /api/sessions, /api/tasks            │
    │   • Static Hosting of Flutter Web Bundle                                │
    └─────────────────────────────────────┬───────────────────────────────────┘
                                          │
                ┌─────────────────────────┼─────────────────────────┐
                ▼                         ▼                         ▼
    ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
    │      SQLite DB        │ │   Accounts Vault      │ │   Antigravity CLI     │
    │  (aiosqlite async)    │ │   ~/.gemini/vault     │ │       (agy.exe)       │
    │ • projects, sessions  │ │ • OAuth 2.0 Direct    │ │ • stream-json mode    │
    │ • scheduled_tasks     │ │ • Windows Keyring     │ │ • multi-model Gemini  │
    │ • task_runs, settings │ │ • 1-click swapping    │ │ • Autonomous engine   │
    └───────────────────────┘ └───────────────────────┘ └───────────────────────┘
```

---

## 🛠 One-Click Installation

The project is packaged as an **All-in-One** self-contained bundle. You don't need to manually configure virtual environments or compile Flutter — the setup wizard handles everything automatically.

### 🐧 Linux / VPS (Ubuntu, Debian, CentOS, Arch, macOS)

**Option A — Direct 1-liner on a clean server (clones and deploys automatically):**
```bash
curl -fsSL https://raw.githubusercontent.com/kobaltgit/gravigram/main/install.sh | bash -s -- https://github.com/kobaltgit/gravigram.git
```

**Option B — Clone and install:**
```bash
git clone https://github.com/kobaltgit/gravigram.git
cd gravigram
bash install.sh
```

**What the installer does automatically:**
1. Installs Python 3.10+, pip, venv, curl, tar, git, and ffmpeg via system package manager (`apt`, `dnf`, `pacman`).
2. Creates virtual environment `venv` and installs dependencies.
3. Automatically detects existing `agy` binary in standard paths (`~/.local/bin/agy`, `/usr/local/bin/agy`) or installs official Antigravity CLI.
4. Unpacks pre-compiled Flutter Web bundle (no Dart/Flutter SDK required on the server).
5. Launches interactive configuration wizard for Bot Token and Admin ID.
6. Configures Nginx reverse proxy with free Let's Encrypt SSL certificate (Certbot).
7. Sets up and starts `systemd` daemon (`gravigram.service`).

---

### 🪟 Windows (Local PC or Windows Server)

**Option A — Direct 1-liner in PowerShell:**
```powershell
irm https://raw.githubusercontent.com/kobaltgit/gravigram/main/install.ps1 | iex
```

**Option B — Clone and install:**
```powershell
git clone https://github.com/kobaltgit/gravigram.git
cd gravigram
powershell -ExecutionPolicy Bypass -File install.ps1
```

**What the installer does automatically:**
1. Checks Python 3.10+ (automatically installs Python 3.11 via `winget` if missing).
2. Initializes `venv`, installs wheels, and unpacks the Web Mini App.
3. Detects `agy.exe` and links Windows Credential Manager (`gemini:antigravity`).
4. Generates `.env` and initializes SQLite database schema.
5. Provides one-click startup scripts (`start_bot.bat`, `start_hidden.vbs`, `stop_bot.bat`).

---

### 🎮 Manual Execution

Run directly using Python:
```bash
python run.py
```
*Starts Telegram long-polling and FastAPI server on `http://0.0.0.0:8000` simultaneously.*

---

### 🐳 Docker / Container Deployment

```bash
docker compose up -d --build
```
*Persists database and uploaded media in `./data` and `./.agy_uploads`.*

---

## 🔑 Google Antigravity Multi-Account Manager

The project features a dedicated account manager (`src/agent/accounts.py`) supporting seamless multi-profile workflows:

1. **Vault Storage**: Account tokens are securely isolated in `~/.gemini/accounts_vault/<email>.json`.
2. **Instant 1-Click Switching**:
   * Tap **«🔑 Аккаунты»** in Telegram chat.
   * Active account is indicated with `✅ email@gmail.com`.
   * Tap `🔄 switch@gmail.com` to swap active profile in **1 second** without restarting or re-entering codes.
3. **Dual Sync (Windows & Linux)**:
   * **Linux / Headless**: Hot-swaps `~/.gemini/oauth_creds.json` and updates `google_accounts.json`.
   * **Windows**: Synchronizes both file credentials and the Windows Credential Manager (`gemini:antigravity` via `Advapi32.dll`), ensuring terminal `agy` and the bot always use the exact same account.
4. **Linking New Accounts**:
   * Click `➕ Войти в новый аккаунт`.
   * **Automatic Local**: If browsing from the same host, the background loopback receiver on `127.0.0.1:8085` automatically intercepts redirect and completes login.
   * **Mobile / Remote Fallback**: If using a smartphone, simply copy the URL from browser address bar (containing `code=...`) or the code itself and send it to the Telegram chat.

---

## 💬 Telegram Bot Commands & Controls

| Command | Description |
| :--- | :--- |
| `/start` | Launch bot, verify access, show welcome dashboard and main keyboard |
| `/help` | Detailed guide for all features, commands, and shortcuts |
| `/projects` | Manage workspaces: create new, switch active, delete folders |
| `/chats` | List conversation sessions within active project, resume previous turns |
| `/new` | Start a fresh clean conversation session |
| `/mode` | Toggle autonomy mode: Full Autonomous (`/auto`) or Confirm Actions (`/confirm`) |
| `/models` | Select Antigravity Gemini model (`gemini-3.7-flash`, `gemini-3.8-flash`, etc.) |
| `/tasks` | Manage scheduled tasks and automated cron routines |
| `/accounts` | Open Google Antigravity Multi-Account Manager and Switcher |
| `/cancel` | Cancel currently running AI generation or shell execution |
| `/quick` | Display quick-action preset buttons |

---

## 📱 Flutter Mini App Interface (TMA)

The Mini App is accessible directly inside Telegram via the **«🚀 Open Mini App»** button or via your configured HTTPS domain:

* **Home Screen**: Agent status indicator, active model, workspace path, autonomy badge, and real-time system metrics (CPU, RAM, Disk).
* **Projects Screen**: Directory tree explorer, file code viewer with syntax highlighting, and workspace switcher.
* **Sessions Screen**: Message history viewer with search, turn inspection, and direct session switching.
* **Tasks Screen**: Interactive scheduled task manager with native Material TimePicker, preset chips (🌅 Morning Audit, 🧪 Run Tests, 🧹 Cleanup), and execution history log dialog.
* **Settings Screen**: Control AI model selection, autonomy toggle, confirmation modes, and environment preferences.

---

## ⏰ Scheduled Tasks & Automation Engine

Run unattended agent routines autonomously:

```bash
# Add a daily routine at 09:00 AM:
python -m src.agent.schedule_cli add --time "09:00" --title "Morning Audit" --prompt "Check server health, docker containers, and disk space"

# List scheduled tasks:
python -m src.agent.schedule_cli list

# Pause or activate a task:
python -m src.agent.schedule_cli toggle --id 1 --active true

# Delete task:
python -m src.agent.schedule_cli delete --id 1
```

*Results are logged to SQLite `task_runs` table and can be inspected in the Mini App.*

---

## ⚙️ Configuration Guide (.env)

| Parameter | Required | Description | Example |
| :--- | :---: | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | **Yes** | Telegram Bot API token from [@BotFather](https://t.me/botfather) | `8841318937:AAFP...` |
| `TELEGRAM_ADMIN_ID` | **Yes** | Your personal Telegram user ID (strict single-user gate) | `123456789` |
| `DEFAULT_MODEL` | No | Default Gemini model for Antigravity engine | `gemini-3.7-flash` |
| `DEFAULT_WORKSPACE_PATH` | No | Initial directory for agent operations | `.` or `/var/www` |
| `CONFIRM_MODE` | No | Require confirmation before shell commands / file writes | `false` |
| `HOST` | No | Host binding for FastAPI REST & Mini App | `0.0.0.0` |
| `PORT` | No | Port for FastAPI REST & Mini App | `8000` |
| `WEBAPP_URL` | No | Public HTTPS URL for Telegram WebApp button | `https://agy.yourdomain.com` |
| `AGY_BIN_PATH` | No | Explicit path to `agy` binary if not in standard PATH | `/usr/local/bin/agy` |
| `TRUSTED_PROXIES` | No | Comma-separated trusted reverse proxy IPs | `127.0.0.1,::1,192.168.5.128` |

---

## 📂 Repository Structure

```
gravigram/
├── .agents/                 # AI Agent instructions, skills, and rules
├── wiki/                    # Obligatory documentation & project trackers
│   ├── activity_log.md      # Chronological log of all code changes
│   ├── bug_tracker.md       # Defect registry with solutions (30+ resolved)
│   ├── checklist.md         # Component readiness checklist
│   ├── roadmap.md           # Visual development phases
│   └── implementation_plan.md
├── frontend_flutter/        # Flutter Web TMA (Dart 3.44+ SPA)
│   ├── lib/
│   │   ├── screens/         # Home, Projects, Sessions, Tasks, Settings
│   │   ├── services/        # ApiService, Telegram WebApp SDK bindings
│   │   └── widgets/         # Glassmorphic cards, charts, file viewer
│   └── web/                 # index.html with Telegram WebApp SDK
├── src/                     # Core Python backend
│   ├── agent/               # Antigravity CLI engine, accounts, scheduler, STT
│   │   ├── accounts.py      # Multi-Account Manager & OAuth 2.0 direct flow
│   │   ├── manager.py       # Process lifecycle & stream-json parser
│   │   ├── scheduler.py     # Background cron automation loop
│   │   └── transcriber.py   # faster-whisper local STT
│   ├── bot/                 # aiogram 3 Telegram Bot
│   │   ├── handlers/        # Chat, photos, files, accounts, callbacks
│   │   ├── middlewares.py   # Strict single-user Admin ID validation
│   │   └── formatter.py     # HTML entity converter
│   └── server/              # FastAPI REST endpoints & TMA static server
├── deploy/                  # systemd service templates
├── data/                    # SQLite database & session storage (gitignored)
├── miniapp_web.tar.gz       # Pre-built release bundle of Flutter Web TMA
├── install.sh               # One-click installer for Linux
├── install.ps1              # One-click installer for Windows
├── setup.py                 # Interactive configuration & setup wizard
└── run.py                   # Main unified backend runner
```

---

## 🧪 Automated Testing

Gravigram features a comprehensive automated test suite covering both the asynchronous Python backend and the Flutter Mini App frontend with **100% pass rate (70 of 70 tests)**:

* **Python Backend** (`pytest`): 59 tests covering SQLite CRUD, Telegram TMA HMAC-SHA256 crypto validation, REST endpoints, `HH:MM` & cron scheduler, agent streaming & hooks, i18n dictionaries parity, and Google OAuth account manager.
* **Flutter Mini App** (`flutter test`): 11 tests covering data models, reactive `LanguageController`, string translations, and widget tests for all app screens (`HomeScreen`, `SettingsScreen`, `ProjectsScreen`, `TasksScreen`).

Run the entire test suite with a single command:

```powershell
# Windows PowerShell:
.\scripts\run_tests.ps1
```

```bash
# Linux / macOS Bash:
bash scripts/run_tests.sh
```

Or run tests individually:
```bash
# Backend unit & integration tests:
pytest -v

# Frontend Flutter tests:
cd frontend_flutter && flutter test
```

---

## 📚 Wiki & Documentation Protocol

All modifications, fixes, and architectural adjustments follow the strict **Wiki Protocol** defined in [`.agents/rules/wiki_rules.md`](file:///.agents/rules/wiki_rules.md):
* **Every change** is documented in [`wiki/activity_log.md`](wiki/activity_log.md).
* **Every feature** is tracked in [`wiki/checklist.md`](wiki/checklist.md).
* **Every bug** is registered and resolved in [`wiki/bug_tracker.md`](wiki/bug_tracker.md).
* Documentation is automatically audited by the built-in `wiki-maintainer` agent.

---

## 📄 License

This project is open-source under the [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE).  
Built with ❤️ for autonomous AI agent development and seamless cloud/home-lab control.

