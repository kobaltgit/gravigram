from datetime import datetime, timedelta
import pytest
from src.agent.scheduler import parse_schedule_expression
from src.database import create_scheduled_task, get_scheduled_task, list_scheduled_tasks

def test_parse_friendly_time_expression():
    now = datetime(2026, 10, 7, 8, 0, 0)
    # 09:00 should be 1 hour later on the same day
    next_run = parse_schedule_expression("09:00", base_time=now)
    assert next_run is not None
    assert next_run.hour == 9
    assert next_run.minute == 0
    assert next_run > now

def test_parse_past_time_rolls_to_next_day():
    now = datetime(2026, 10, 7, 10, 0, 0)
    # 09:00 has already passed today, so next run should be tomorrow at 09:00
    next_run = parse_schedule_expression("09:00", base_time=now)
    assert next_run is not None
    assert next_run.hour == 9
    assert next_run.day == 8
    assert next_run > now

def test_parse_standard_cron_expression():
    now = datetime(2026, 10, 7, 12, 0, 0)
    # Every 15 minutes: "*/15 * * * *"
    next_run = parse_schedule_expression("*/15 * * * *", base_time=now)
    assert next_run is not None
    assert next_run == datetime(2026, 10, 7, 12, 15, 0)

def test_parse_invalid_expression():
    assert parse_schedule_expression("not_a_valid_cron_time") is None
    assert parse_schedule_expression("") is None

@pytest.mark.asyncio
async def test_scheduler_task_creation_with_parsed_expression():
    expr = "14:30"
    next_dt = parse_schedule_expression(expr)
    assert next_dt is not None

    task = await create_scheduled_task(
        title="Check Server Logs",
        cron_expression=expr,
        prompt="Audit server logs and check error count",
        next_run_at=next_dt.isoformat()
    )
    assert task["id"] > 0
    assert task["next_run_at"] == next_dt.isoformat()

    retrieved = await get_scheduled_task(task["id"])
    assert retrieved["title"] == "Check Server Logs"
