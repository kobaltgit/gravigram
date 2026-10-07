import pytest
from src.database import (
    list_projects, add_project, set_active_project, get_active_project, delete_project,
    list_sessions, create_session, get_active_session, set_active_session, delete_session,
    get_setting, set_setting,
    list_db_models, add_db_model, delete_db_model,
    create_scheduled_task, list_scheduled_tasks, get_scheduled_task, toggle_scheduled_task, delete_scheduled_task, update_task_run_timestamps,
    get_language, set_language
)

pytestmark = pytest.mark.asyncio

async def test_projects_crud():
    # Initially default project should be present
    projects = await list_projects()
    assert len(projects) >= 1
    default_proj = await get_active_project()
    assert default_proj is not None

    # Add a new project
    p2 = await add_project(name="Custom Project", path="/path/to/custom", make_active=True)
    assert p2["name"] == "Custom Project"
    assert p2["is_active"] == 1

    active = await get_active_project()
    assert active["name"] == "Custom Project"
    assert active["path"] == p2["path"]

    # Switch back to first project
    switched = await set_active_project(default_proj["id"])
    assert switched is True
    active_now = await get_active_project()
    assert active_now["id"] == default_proj["id"]

    # Delete project
    del_ok = await delete_project(p2["id"])
    assert del_ok is True
    all_projs = await list_projects()
    assert not any(p["id"] == p2["id"] for p in all_projs)


async def test_sessions_crud():
    proj = await get_active_project()
    proj_id = proj["id"]

    # Create session 1
    s1 = await create_session(project_id=proj_id, title="Session Alpha", conversation_id="conv-aaa", make_active=True)
    assert s1["title"] == "Session Alpha"
    assert s1["is_active"] == 1

    active = await get_active_session(proj_id)
    assert active["id"] == s1["id"]

    # Create session 2
    s2 = await create_session(project_id=proj_id, title="Session Beta", conversation_id="conv-bbb", make_active=True)
    active2 = await get_active_session(proj_id)
    assert active2["id"] == s2["id"]

    # List sessions
    sessions = await list_sessions(proj_id)
    assert len(sessions) == 2

    # Switch active session
    await set_active_session(s1["id"])
    active_reloaded = await get_active_session(proj_id)
    assert active_reloaded["id"] == s1["id"]

    # Delete session
    del_res = await delete_session(s2["id"])
    assert del_res is True
    sessions_after = await list_sessions(proj_id)
    assert len(sessions_after) == 1


async def test_settings_and_language():
    # Check default setting
    confirm = await get_setting("confirm_mode")
    assert confirm == "false"

    # Update setting
    await set_setting("confirm_mode", "true")
    assert await get_setting("confirm_mode") == "true"

    # Language setting
    lang = await get_language()
    assert lang in ("ru", "en")

    await set_language("en")
    assert await get_language() == "en"

    await set_language("ru")
    assert await get_language() == "ru"


async def test_models_management():
    models = await list_db_models()
    assert len(models) >= 5

    # Switch model via settings
    target_model = "gemini-3.7-flash"
    await set_setting("active_model", target_model)
    assert await get_setting("active_model") == target_model

    # Add custom model
    new_m = await add_db_model("custom-model-x", "Custom Model X", "Test description", is_custom=True)
    assert new_m["id"] == "custom-model-x"

    models_after = await list_db_models()
    assert any(m["id"] == "custom-model-x" for m in models_after)

    # Delete custom model
    deleted = await delete_db_model("custom-model-x")
    assert deleted is True


async def test_scheduled_tasks_lifecycle():
    proj = await get_active_project()

    # Add task
    task = await create_scheduled_task(
        title="Nightly Build",
        cron_expression="0 2 * * *",
        prompt="Run automated tests and generate report",
        project_id=proj["id"]
    )
    assert task["id"] > 0
    assert task["title"] == "Nightly Build"
    assert task["is_active"] == 1

    # List tasks
    all_tasks = await list_scheduled_tasks()
    assert any(t["id"] == task["id"] for t in all_tasks)

    # Toggle task
    toggled = await toggle_scheduled_task(task["id"], False)
    assert toggled is True
    t_obj = await get_scheduled_task(task["id"])
    assert t_obj["is_active"] == 0

    toggled_back = await toggle_scheduled_task(task["id"], True)
    assert toggled_back is True
    t_obj2 = await get_scheduled_task(task["id"])
    assert t_obj2["is_active"] == 1

    # Update task run timestamps
    await update_task_run_timestamps(task["id"], "2026-10-07 02:00:00")
    t_obj3 = await get_scheduled_task(task["id"])
    assert t_obj3["last_run_at"] == "2026-10-07 02:00:00"

    # Delete task
    del_ok = await delete_scheduled_task(task["id"])
    assert del_ok is True
    assert not any(t["id"] == task["id"] for t in await list_scheduled_tasks())

