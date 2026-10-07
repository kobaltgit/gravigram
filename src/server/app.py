import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config import settings
from src.agent.models import get_available_models, register_new_model, remove_model
from src.database import (
    list_projects, get_active_project, get_project, add_project, set_active_project, delete_project,
    list_sessions, get_active_session, create_session, set_active_session, delete_session,
    get_setting, set_setting,
    list_scheduled_tasks, get_scheduled_task, create_scheduled_task, update_scheduled_task, toggle_scheduled_task, delete_scheduled_task,
    list_task_runs, get_session_messages
)
from src.agent.scheduler import agent_scheduler, parse_schedule_expression
from src.server.auth import verify_admin_access

app = FastAPI(title="Antigravity Mini App API", version="1.0.0")

# Enable CORS for Flutter Web / Telegram WebApp
# NOTE: allow_credentials is False because auth uses Bearer/header tokens, not cookies.
# Combining allow_origins=["*"] with allow_credentials=True is invalid per the Fetch spec.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Request Schemas ---

class CreateProjectRequest(BaseModel):
    name: str
    path: str
    make_active: bool = True

class CreateSessionRequest(BaseModel):
    project_id: Optional[int] = None
    title: str = "Новая беседа"
    make_active: bool = True

class SettingUpdateRequest(BaseModel):
    key: str
    value: str

class CreateModelRequest(BaseModel):
    id: str
    name: str
    description: str = ""

class CreateTaskRequest(BaseModel):
    title: str
    cron_expression: str
    prompt: str
    project_id: Optional[int] = None

class UpdateTaskRequest(BaseModel):
    title: str
    cron_expression: str
    prompt: str
    project_id: Optional[int] = None

class ToggleTaskRequest(BaseModel):
    is_active: bool

# --- REST API Endpoints (Secured with verify_admin_access) ---

@app.get("/api/status", dependencies=[Depends(verify_admin_access)])
async def get_system_status():
    active_project = await get_active_project()
    active_session = await get_active_session(active_project["id"] if active_project else None)
    confirm_mode = (await get_setting("confirm_mode", "false")).lower() == "true"
    model = await get_setting("model", "")
    tasks = await list_scheduled_tasks(active_only=True)
    return {
        "status": "online",
        "active_project": active_project,
        "active_session": active_session,
        "confirm_mode": confirm_mode,
        "model": model,
        "active_tasks_count": len(tasks),
    }

@app.get("/api/models", dependencies=[Depends(verify_admin_access)])
async def api_get_models():
    models = await get_available_models()
    current_model = await get_setting("model", "")
    return {
        "models": models,
        "current_model": current_model
    }

@app.post("/api/models", dependencies=[Depends(verify_admin_access)])
async def api_create_model(req: CreateModelRequest):
    model = await register_new_model(model_id=req.id, name=req.name, description=req.description)
    return {"success": True, "model": model}

@app.delete("/api/models/{model_id}", dependencies=[Depends(verify_admin_access)])
async def api_delete_model(model_id: str):
    success = await remove_model(model_id)
    return {"success": success}

# --- Scheduled Agent Tasks API ---

@app.get("/api/tasks", dependencies=[Depends(verify_admin_access)])
async def api_list_tasks():
    return await list_scheduled_tasks()

@app.post("/api/tasks", dependencies=[Depends(verify_admin_access)])
async def api_create_task(req: CreateTaskRequest):
    next_run = parse_schedule_expression(req.cron_expression)
    next_run_str = next_run.isoformat() if next_run else None
    task = await create_scheduled_task(
        title=req.title,
        cron_expression=req.cron_expression,
        prompt=req.prompt,
        project_id=req.project_id,
        next_run_at=next_run_str
    )
    return task

@app.put("/api/tasks/{task_id}", dependencies=[Depends(verify_admin_access)])
async def api_update_task(task_id: int, req: UpdateTaskRequest):
    next_run = parse_schedule_expression(req.cron_expression)
    next_run_str = next_run.isoformat() if next_run else None
    task = await update_scheduled_task(
        task_id=task_id,
        title=req.title,
        cron_expression=req.cron_expression,
        prompt=req.prompt,
        project_id=req.project_id,
        next_run_at=next_run_str
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/api/tasks/{task_id}/toggle", dependencies=[Depends(verify_admin_access)])
async def api_toggle_task(task_id: int, req: ToggleTaskRequest):
    success = await toggle_scheduled_task(task_id, req.is_active)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "is_active": req.is_active}

@app.post("/api/tasks/{task_id}/run", dependencies=[Depends(verify_admin_access)])
async def api_run_task(task_id: int):
    task = await get_scheduled_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    asyncio.create_task(agent_scheduler.run_task(task_id))
    return {"success": True, "message": f"Task #{task_id} launched"}

@app.delete("/api/tasks/{task_id}", dependencies=[Depends(verify_admin_access)])
async def api_delete_task(task_id: int):
    success = await delete_scheduled_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}

@app.get("/api/task_runs", dependencies=[Depends(verify_admin_access)])
async def api_list_all_task_runs(limit: int = 50):
    return await list_task_runs(limit=limit)

@app.get("/api/tasks/{task_id}/runs", dependencies=[Depends(verify_admin_access)])
async def api_list_task_runs(task_id: int, limit: int = 50):
    return await list_task_runs(task_id=task_id, limit=limit)

# --- Projects API ---

@app.get("/api/projects", dependencies=[Depends(verify_admin_access)])
async def api_list_projects():
    return await list_projects()

@app.post("/api/projects", dependencies=[Depends(verify_admin_access)])
async def api_create_project(req: CreateProjectRequest):
    if not os.path.exists(req.path):
        try:
            os.makedirs(req.path, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cannot create directory: {str(e)}")
    project = await add_project(name=req.name, path=req.path, make_active=req.make_active)
    return project

@app.post("/api/projects/{project_id}/activate", dependencies=[Depends(verify_admin_access)])
async def api_activate_project(project_id: int):
    success = await set_active_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True, "active_project": await get_active_project()}

@app.delete("/api/projects/{project_id}", dependencies=[Depends(verify_admin_access)])
async def api_delete_project(project_id: int):
    success = await delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True}

@app.get("/api/projects/{project_id}/files", dependencies=[Depends(verify_admin_access)])
async def api_get_project_files(project_id: int, subdir: str = ""):
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    base_path = Path(project["path"]).resolve()
    if not base_path.exists() or not base_path.is_dir():
        raise HTTPException(status_code=400, detail="Project directory does not exist on disk")

    target_path = (base_path / subdir.lstrip("/\\")).resolve()
    # Path traversal check
    if not str(target_path).startswith(str(base_path)):
        raise HTTPException(status_code=403, detail="Access denied: path outside project workspace")

    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    items = []
    ignored_names = {".git", ".venv", "venv", "__pycache__", "node_modules", ".dart_tool", "build"}
    try:
        with os.scandir(target_path) as entries:
            for entry in entries:
                if entry.name in ignored_names:
                    continue
                try:
                    stat = entry.stat()
                    rel_path = str(Path(entry.path).relative_to(base_path)).replace("\\", "/")
                    items.append({
                        "name": entry.name,
                        "path": rel_path,
                        "is_dir": entry.is_dir(),
                        "size": stat.st_size if not entry.is_dir() else 0,
                        "modified_at": stat.st_mtime
                    })
                except OSError:
                    continue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot read directory: {str(e)}")

    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    rel_current = str(target_path.relative_to(base_path)).replace("\\", "/")
    if rel_current == ".":
        rel_current = ""

    return {
        "project_id": project_id,
        "current_subdir": rel_current,
        "items": items
    }

@app.get("/api/projects/{project_id}/file_content", dependencies=[Depends(verify_admin_access)])
async def api_get_project_file_content(project_id: int, file_path: str):
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    base_path = Path(project["path"]).resolve()
    target_file = (base_path / file_path.lstrip("/\\")).resolve()
    if not str(target_file).startswith(str(base_path)):
        raise HTTPException(status_code=403, detail="Access denied: path outside project workspace")

    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    max_size = 1024 * 1024  # 1 MB
    stat = target_file.stat()
    if stat.st_size > max_size:
        raise HTTPException(status_code=400, detail=f"File too large for preview ({stat.st_size} bytes, max 1MB)")

    try:
        content = target_file.read_text(encoding="utf-8", errors="replace")
        return {
            "name": target_file.name,
            "path": file_path,
            "size": stat.st_size,
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot read file: {str(e)}")

# --- Sessions API ---

@app.get("/api/sessions", dependencies=[Depends(verify_admin_access)])
async def api_list_sessions(project_id: Optional[int] = None):
    if project_id is None:
        active_proj = await get_active_project()
        project_id = active_proj["id"] if active_proj else None
    return await list_sessions(project_id=project_id)

@app.post("/api/sessions", dependencies=[Depends(verify_admin_access)])
async def api_create_session(req: CreateSessionRequest):
    proj_id = req.project_id
    if proj_id is None:
        active_proj = await get_active_project()
        if not active_proj:
            raise HTTPException(status_code=400, detail="No active project available")
        proj_id = active_proj["id"]

    conv_id = str(uuid.uuid4())
    session = await create_session(
        project_id=proj_id,
        title=req.title,
        conversation_id=conv_id,
        make_active=req.make_active
    )
    return session

@app.post("/api/sessions/{session_id}/activate", dependencies=[Depends(verify_admin_access)])
async def api_activate_session(session_id: int):
    success = await set_active_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True}

@app.delete("/api/sessions/{session_id}", dependencies=[Depends(verify_admin_access)])
async def api_delete_session(session_id: int):
    success = await delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True}

@app.get("/api/sessions/{session_id}/messages", dependencies=[Depends(verify_admin_access)])
async def api_get_session_messages(session_id: int, limit: int = 100):
    return await get_session_messages(session_id=session_id, limit=limit)

# --- Settings API ---

@app.get("/api/settings", dependencies=[Depends(verify_admin_access)])
async def api_get_settings():
    confirm_mode = await get_setting("confirm_mode", "false")
    model = await get_setting("model", "")
    language = await get_setting("language", "ru")
    return {
        "confirm_mode": confirm_mode.lower() == "true",
        "model": model,
        "language": language or "ru"
    }

@app.post("/api/settings", dependencies=[Depends(verify_admin_access)])
async def api_update_settings(req: SettingUpdateRequest):
    await set_setting(req.key, req.value)
    return {"success": True, "key": req.key, "value": req.value}

# --- Static Flutter Web Mounting (SPA Fallback) ---

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "frontend_flutter" / "build" / "web"

class SPAStaticFiles(StaticFiles):
    """StaticFiles handler that falls back to index.html for SPA client-side routes."""
    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
            if response.status_code == 404:
                return await super().get_response("index.html", scope)
            return response
        except HTTPException as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            raise

if WEB_DIR.exists():
    app.mount("/", SPAStaticFiles(directory=str(WEB_DIR), html=True), name="flutter_web")
