import sys
import argparse
import asyncio
from src.database import (
    init_db, list_scheduled_tasks, create_scheduled_task,
    delete_scheduled_task, toggle_scheduled_task, get_active_project
)
from src.agent.scheduler import parse_schedule_expression

async def main():
    parser = argparse.ArgumentParser(description="Antigravity Scheduler CLI Helper for Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add task
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--time", required=True, help="Time e.g. 09:00 or cron '0 9 * * *'")
    add_parser.add_argument("--prompt", required=True, help="Prompt instruction for the agent")
    add_parser.add_argument("--title", default="", help="Optional title")

    # List tasks
    subparsers.add_parser("list")

    # Delete task
    del_parser = subparsers.add_parser("delete")
    del_parser.add_argument("--id", type=int, required=True, help="Task ID")

    # Toggle task
    toggle_parser = subparsers.add_parser("toggle")
    toggle_parser.add_argument("--id", type=int, required=True, help="Task ID")
    toggle_parser.add_argument("--active", type=str, required=True, choices=["true", "false"])

    args = parser.parse_args()
    await init_db()

    if args.command == "add":
        title = args.title.strip() or args.prompt[:30] + ("..." if len(args.prompt) > 30 else "")
        active_proj = await get_active_project()
        proj_id = active_proj["id"] if active_proj else None
        
        next_run = parse_schedule_expression(args.time)
        next_str = next_run.isoformat() if next_run else None

        task = await create_scheduled_task(
            title=title,
            cron_expression=args.time,
            prompt=args.prompt,
            project_id=proj_id,
            next_run_at=next_str
        )
        print(f"SUCCESS: Created task #{task['id']}: '{task['title']}' for time '{task['cron_expression']}' (Next: {next_str})")

    elif args.command == "list":
        tasks = await list_scheduled_tasks()
        print(f"Total scheduled tasks: {len(tasks)}")
        for t in tasks:
            status = "ACTIVE" if t.get("is_active") else "PAUSED"
            print(f"#{t['id']} [{status}] [{t['cron_expression']}] {t['title']} -> {t['prompt']}")

    elif args.command == "delete":
        success = await delete_scheduled_task(args.id)
        print(f"{'SUCCESS' if success else 'FAILED'}: Task #{args.id} deleted.")

    elif args.command == "toggle":
        is_act = args.active.lower() == "true"
        success = await toggle_scheduled_task(args.id, is_act)
        print(f"{'SUCCESS' if success else 'FAILED'}: Task #{args.id} set active={is_act}.")

if __name__ == "__main__":
    asyncio.run(main())
