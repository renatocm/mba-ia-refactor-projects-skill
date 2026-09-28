"""Report use cases; payloads retain the existing HTTP representation."""
from datetime import timedelta

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from services.exceptions import NotFound
from utils.time import utc_now


def summary_report():
    tasks = Task.query.all()
    users = User.query.all()
    category_count = Category.query.count()
    by_status = {
        status: sum(task.status == status for task in tasks)
        for status in ("pending", "in_progress", "done", "cancelled")
    }
    by_priority = {
        str(priority): sum(task.priority == priority for task in tasks)
        for priority in range(1, 6)
    }
    overdue = [
        {"id": task.id, "title": task.title, "due_date": task.due_date.isoformat()}
        for task in tasks if task.to_dict()["overdue"]
    ]
    productivity = []
    for user in users:
        own_tasks = [task for task in tasks if task.user_id == user.id]
        done = sum(task.status == "done" for task in own_tasks)
        productivity.append({
            "user_id": user.id,
            "user_name": user.name,
            "total_tasks": len(own_tasks),
            "completed_tasks": done,
            "completion_rate": round(done / len(own_tasks) * 100, 2) if own_tasks else 0,
        })
    seven_days_ago = utc_now() - timedelta(days=7)
    recent_created = sum(
        bool(task.created_at and task.created_at.replace(
            tzinfo=task.created_at.tzinfo or utc_now().tzinfo) >= seven_days_ago)
        for task in tasks
    )
    recent_done = sum(
        bool(task.status == "done" and task.updated_at and task.updated_at.replace(
            tzinfo=task.updated_at.tzinfo or utc_now().tzinfo) >= seven_days_ago)
        for task in tasks
    )
    return {
        "generated_at": utc_now().isoformat(),
        "overview": {
            "total_tasks": len(tasks), "total_users": len(users),
            "total_categories": category_count,
        },
        "tasks_by_status": by_status,
        "tasks_by_priority": {
            "critical": by_priority["1"], "high": by_priority["2"],
            "medium": by_priority["3"], "low": by_priority["4"],
            "minimal": by_priority["5"],
        },
        "overdue": {"count": len(overdue), "tasks": overdue},
        "recent_activity": {
            "tasks_created_last_7_days": recent_created,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": productivity,
    }


def user_report(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFound("Usuário não encontrado")
    tasks = Task.query.filter_by(user_id=user_id).all()
    done = sum(task.status == "done" for task in tasks)
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": len(tasks),
            "done": done,
            "pending": sum(task.status == "pending" for task in tasks),
            "in_progress": sum(task.status == "in_progress" for task in tasks),
            "cancelled": sum(task.status == "cancelled" for task in tasks),
            "overdue": sum(task.to_dict()["overdue"] for task in tasks),
            "high_priority": sum(task.priority <= 2 for task in tasks),
            "completion_rate": round(done / len(tasks) * 100, 2) if tasks else 0,
        },
    }
