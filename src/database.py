import os
import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
from src.config import settings

DB_FILE = Path(settings.db_path)

@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON;")
        yield db

DEFAULT_INITIAL_MODELS = [
    ("", "⚡ По умолчанию (Antigravity Auto)", "Текущая активная модель из настроек Antigravity", 0),
    ("gemini-3.7-flash", "Gemini 3.7 Flash", "High reasoning effort (основная модель)", 0),
    ("gemini-3.6-flash", "Gemini 3.6 Flash", "Medium reasoning effort (быстрая)", 0),
    ("gemini-3.5-flash", "Gemini 3.5 Flash", "Medium reasoning effort (быстрая)", 0),
    ("gemini-3.1-pro", "Gemini 3.1 Pro", "Low reasoning effort", 0),
    ("claude-sonnet-4.6", "Claude Sonnet 4.6", "Thinking mode (глубокий анализ кода)", 0),
    ("claude-opus-4.6", "Claude Opus 4.6", "Thinking mode (сложные архитектурные задачи)", 0),
    ("gpt-oss-120b", "GPT-OSS 120B", "Medium effort open-source модель", 0),
]

async def init_db(default_project_path: Optional[str] = None, default_project_name: str = "Antigravity Project") -> None:
    """Initialize database tables and create defaults if none exist."""
    async with get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 0
            );
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                conversation_id TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                is_custom INTEGER DEFAULT 0
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                cron_expression TEXT NOT NULL,
                prompt TEXT NOT NULL,
                project_id INTEGER,
                is_active INTEGER DEFAULT 1,
                last_run_at TIMESTAMP,
                next_run_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS session_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'running',
                execution_time_seconds REAL DEFAULT 0,
                output_preview TEXT DEFAULT '',
                error_message TEXT DEFAULT '',
                FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id) ON DELETE CASCADE
            );
        """)
        await db.commit()

        # Seed models if table is empty
        async with db.execute("SELECT COUNT(*) as cnt FROM models;") as cursor:
            row = await cursor.fetchone()
            if row["cnt"] == 0:
                for m_id, m_name, m_desc, is_c in DEFAULT_INITIAL_MODELS:
                    await db.execute(
                        "INSERT OR IGNORE INTO models (id, name, description, is_custom) VALUES (?, ?, ?, ?);",
                        (m_id, m_name, m_desc, is_c)
                    )
                await db.commit()

        # Check if any project exists, if not create default
        async with db.execute("SELECT COUNT(*) as cnt FROM projects;") as cursor:
            row = await cursor.fetchone()
            if row["cnt"] == 0:
                path = default_project_path or settings.default_workspace_path
                await db.execute(
                    "INSERT INTO projects (name, path, is_active) VALUES (?, ?, 1);",
                    (default_project_name, str(Path(path).resolve()))
                )
                await db.commit()

        # Check if settings exist, if not initialize defaults
        defaults = {
            "confirm_mode": str(settings.confirm_mode).lower(),
            "model": settings.default_model,
            "language": "ru",
        }
        for k, v in defaults.items():
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);",
                (k, v)
            )
        await db.commit()

# --- Project Operations ---

async def list_projects() -> List[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute("SELECT * FROM projects ORDER BY is_active DESC, created_at DESC;") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_active_project() -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute("SELECT * FROM projects WHERE is_active = 1 LIMIT 1;") as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_project(project_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute("SELECT * FROM projects WHERE id = ? LIMIT 1;", (project_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def add_project(name: str, path: str, make_active: bool = True) -> Dict[str, Any]:
    resolved_path = str(Path(path).resolve())
    async with get_db() as db:
        if make_active:
            await db.execute("UPDATE projects SET is_active = 0;")
        
        await db.execute(
            "INSERT INTO projects (name, path, is_active) VALUES (?, ?, ?);",
            (name, resolved_path, 1 if make_active else 0)
        )
        await db.commit()
        
        async with db.execute("SELECT * FROM projects WHERE path = ?;", (resolved_path,)) as cursor:
            row = await cursor.fetchone()
            return dict(row)

async def set_active_project(project_id: int) -> bool:
    async with get_db() as db:
        await db.execute("UPDATE projects SET is_active = 0;")
        cursor = await db.execute("UPDATE projects SET is_active = 1 WHERE id = ?;", (project_id,))
        await db.commit()
        return cursor.rowcount > 0

async def delete_project(project_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM projects WHERE id = ?;", (project_id,))
        await db.commit()
        return cursor.rowcount > 0

# --- Session Operations ---

async def list_sessions(project_id: Optional[int] = None) -> List[Dict[str, Any]]:
    async with get_db() as db:
        if project_id is not None:
            query = "SELECT * FROM sessions WHERE project_id = ? ORDER BY is_active DESC, updated_at DESC;"
            params = (project_id,)
        else:
            query = "SELECT * FROM sessions ORDER BY is_active DESC, updated_at DESC;"
            params = ()
            
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_active_session(project_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        if project_id is not None:
            query = "SELECT * FROM sessions WHERE project_id = ? AND is_active = 1 LIMIT 1;"
            params = (project_id,)
        else:
            query = "SELECT * FROM sessions WHERE is_active = 1 LIMIT 1;"
            params = ()
            
        async with db.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def create_session(project_id: int, title: str, conversation_id: str, make_active: bool = True) -> Dict[str, Any]:
    async with get_db() as db:
        if make_active:
            await db.execute("UPDATE sessions SET is_active = 0 WHERE project_id = ?;", (project_id,))
            
        await db.execute(
            "INSERT INTO sessions (project_id, title, conversation_id, is_active) VALUES (?, ?, ?, ?);",
            (project_id, title, conversation_id, 1 if make_active else 0)
        )
        await db.commit()
        
        async with db.execute("SELECT * FROM sessions WHERE conversation_id = ?;", (conversation_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row)

async def set_active_session(session_id: int) -> bool:
    async with get_db() as db:
        async with db.execute("SELECT project_id FROM sessions WHERE id = ?;", (session_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            project_id = row["project_id"]
            
        await db.execute("UPDATE sessions SET is_active = 0 WHERE project_id = ?;", (project_id,))
        cursor = await db.execute("UPDATE sessions SET is_active = 1 WHERE id = ?;", (session_id,))
        await db.commit()
        return cursor.rowcount > 0

async def update_session_title(session_id: int, title: str) -> bool:
    async with get_db() as db:
        cursor = await db.execute(
            "UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
            (title, session_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def delete_session(session_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM sessions WHERE id = ?;", (session_id,))
        await db.commit()
        return cursor.rowcount > 0

# --- Settings Operations ---

async def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    async with get_db() as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?;", (key,)) as cursor:
            row = await cursor.fetchone()
            return row["value"] if row else default

async def set_setting(key: str, value: str) -> None:
    async with get_db() as db:
        await db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value;",
            (key, value)
        )
        await db.commit()

async def get_language() -> str:
    lang = await get_setting("language", "ru")
    return lang.lower() if lang and lang.lower() in ("ru", "en") else "ru"

async def set_language(lang: str) -> None:
    if lang.lower() in ("ru", "en"):
        await set_setting("language", lang.lower())

# --- Models Operations ---

async def list_db_models() -> List[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute("SELECT * FROM models ORDER BY is_custom ASC, id ASC;") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def add_db_model(model_id: str, name: str, description: str = "", is_custom: bool = True) -> Dict[str, Any]:
    async with get_db() as db:
        await db.execute(
            "INSERT INTO models (id, name, description, is_custom) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, description=excluded.description;",
            (model_id, name, description, 1 if is_custom else 0)
        )
        await db.commit()
        async with db.execute("SELECT * FROM models WHERE id = ?;", (model_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row)

async def delete_db_model(model_id: str) -> bool:
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM models WHERE id = ?;", (model_id,))
        await db.commit()
        return cursor.rowcount > 0

# --- Scheduled Agent Tasks Operations ---

async def list_scheduled_tasks(active_only: bool = False) -> List[Dict[str, Any]]:
    async with get_db() as db:
        if active_only:
            query = """
                SELECT t.*, p.name as project_name, p.path as project_path 
                FROM scheduled_tasks t 
                LEFT JOIN projects p ON t.project_id = p.id 
                WHERE t.is_active = 1 
                ORDER BY t.id ASC;
            """
        else:
            query = """
                SELECT t.*, p.name as project_name, p.path as project_path 
                FROM scheduled_tasks t 
                LEFT JOIN projects p ON t.project_id = p.id 
                ORDER BY t.is_active DESC, t.id ASC;
            """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_scheduled_task(task_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        query = """
            SELECT t.*, p.name as project_name, p.path as project_path 
            FROM scheduled_tasks t 
            LEFT JOIN projects p ON t.project_id = p.id 
            WHERE t.id = ?;
        """
        async with db.execute(query, (task_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def create_scheduled_task(
    title: str,
    cron_expression: str,
    prompt: str,
    project_id: Optional[int] = None,
    next_run_at: Optional[str] = None
) -> Dict[str, Any]:
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO scheduled_tasks (title, cron_expression, prompt, project_id, is_active, next_run_at)
            VALUES (?, ?, ?, ?, 1, ?);
            """,
            (title, cron_expression, prompt, project_id, next_run_at)
        )
        task_id = cursor.lastrowid
        await db.commit()
        return await get_scheduled_task(task_id)

async def toggle_scheduled_task(task_id: int, is_active: bool) -> bool:
    async with get_db() as db:
        cursor = await db.execute(
            "UPDATE scheduled_tasks SET is_active = ? WHERE id = ?;",
            (1 if is_active else 0, task_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def update_scheduled_task(
    task_id: int,
    title: str,
    cron_expression: str,
    prompt: str,
    project_id: Optional[int] = None,
    next_run_at: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        await db.execute(
            """
            UPDATE scheduled_tasks 
            SET title = ?, cron_expression = ?, prompt = ?, project_id = ?, next_run_at = ?
            WHERE id = ?;
            """,
            (title, cron_expression, prompt, project_id, next_run_at, task_id)
        )
        await db.commit()
        return await get_scheduled_task(task_id)

async def update_task_run_timestamps(task_id: int, last_run: str, next_run: Optional[str] = None) -> bool:
    async with get_db() as db:
        cursor = await db.execute(
            "UPDATE scheduled_tasks SET last_run_at = ?, next_run_at = ? WHERE id = ?;",
            (last_run, next_run, task_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def delete_scheduled_task(task_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM scheduled_tasks WHERE id = ?;", (task_id,))
        await db.commit()
        return cursor.rowcount > 0

# --- Session Dialogue Memory (Sliding Window) ---

async def add_session_message(session_id: int, role: str, content: str) -> None:
    """Saves a user or assistant message to the session's clean dialogue history."""
    if not session_id or not content:
        return
    async with get_db() as db:
        await db.execute(
            "INSERT INTO session_messages (session_id, role, content) VALUES (?, ?, ?);",
            (session_id, role, content.strip())
        )
        await db.commit()

async def get_session_messages(session_id: int, limit: int = 6) -> List[Dict[str, Any]]:
    """
    Returns the most recent N messages for the session in chronological order (oldest first).
    """
    if not session_id:
        return []
    async with get_db() as db:
        query = """
            SELECT role, content, created_at 
            FROM session_messages 
            WHERE session_id = ? 
            ORDER BY id DESC 
            LIMIT ?;
        """
        async with db.execute(query, (session_id, limit)) as cursor:
            rows = await cursor.fetchall()
            messages = [dict(r) for r in rows]
            messages.reverse() # Chronological order
            return messages

async def clear_session_messages(session_id: int) -> None:
    """Clears dialogue history for a session."""
    if not session_id:
        return
    async with get_db() as db:
        await db.execute("DELETE FROM session_messages WHERE session_id = ?;", (session_id,))
        await db.commit()


# --- Scheduled Task Execution History (task_runs) ---

async def create_task_run(task_id: int) -> int:
    """Creates a new task run record and returns its ID."""
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO task_runs (task_id, status) VALUES (?, 'running');",
            (task_id,)
        )
        await db.commit()
        return cursor.lastrowid

async def finish_task_run(
    run_id: int,
    status: str,
    execution_time_seconds: float,
    output_preview: str = "",
    error_message: str = ""
) -> None:
    """Updates a task run record with the final execution status and timing."""
    now_iso = datetime.now().isoformat()
    # Trim output preview to avoid massive database bloat
    preview = output_preview[:4000] if output_preview else ""
    async with get_db() as db:
        await db.execute(
            """
            UPDATE task_runs
            SET finished_at = ?,
                status = ?,
                execution_time_seconds = ?,
                output_preview = ?,
                error_message = ?
            WHERE id = ?;
            """,
            (now_iso, status, execution_time_seconds, preview, error_message, run_id)
        )
        await db.commit()

async def list_task_runs(task_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Lists task execution history in reverse chronological order."""
    async with get_db() as db:
        if task_id is not None:
            query = """
                SELECT tr.*, st.title as task_title
                FROM task_runs tr
                LEFT JOIN scheduled_tasks st ON tr.task_id = st.id
                WHERE tr.task_id = ?
                ORDER BY tr.id DESC
                LIMIT ?;
            """
            params = (task_id, limit)
        else:
            query = """
                SELECT tr.*, st.title as task_title
                FROM task_runs tr
                LEFT JOIN scheduled_tasks st ON tr.task_id = st.id
                ORDER BY tr.id DESC
                LIMIT ?;
            """
            params = (limit,)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

