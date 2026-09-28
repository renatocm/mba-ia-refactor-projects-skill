from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.validation import validate_task
from utils.time import parse_date,utc_now
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from services.exceptions import NotFound, InvalidInput
from services.transactions import transactional

def list_tasks(): return [task.to_dict() for task in Task.query.options(joinedload(Task.user),joinedload(Task.category)).all()]
def require_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFound("Task não encontrada")
    return task

def get_task(task_id):
    return require_task(task_id).to_dict()
@transactional
def create(data):
    validate_task(data); task=Task(title=data["title"].strip(),description=data.get("description",""),status=data.get("status","pending"),priority=data.get("priority",3),user_id=data.get("user_id"),category_id=data.get("category_id"),tags=",".join(data.get("tags",[])))
    if data.get("due_date"): task.due_date=parse_date(data["due_date"])
    if task.user_id and not db.session.get(User,task.user_id): raise NotFound("Usuário não encontrado")
    if task.category_id and not db.session.get(Category,task.category_id): raise NotFound("Categoria não encontrada")
    db.session.add(task); db.session.flush(); db.session.refresh(task); return task.to_dict()
@transactional
def update(task_id,data):
    task = require_task(task_id)
    validate_task(data,True)
    if data.get("user_id") and not db.session.get(User,data["user_id"]): raise NotFound("Usuário não encontrado")
    if data.get("category_id") and not db.session.get(Category,data["category_id"]): raise NotFound("Categoria não encontrada")
    for key in ("title","description","status","priority","user_id","category_id"):
        if key in data: setattr(task,key,data[key])
    if "tags" in data: task.tags=",".join(data["tags"] or [])
    if "due_date" in data: task.due_date=parse_date(data["due_date"]) if data["due_date"] else None
    task.updated_at=utc_now(); db.session.flush(); db.session.refresh(task); return task.to_dict()


@transactional
def delete(task_id):
    db.session.delete(require_task(task_id))


def search(q="", status=None, priority=None):
    query = Task.query
    if q:
        query = query.filter(or_(Task.title.ilike(f"%{q}%"), Task.description.ilike(f"%{q}%")))
    if status:
        query = query.filter_by(status=status)
    if priority:
        try:
            priority = int(priority)
        except ValueError as error:
            raise InvalidInput("Prioridade inválida") from error
        query = query.filter_by(priority=priority)
    return [task.to_dict() for task in query.all()]


def stats():
    tasks = Task.query.all()
    return {
        "total": len(tasks),
        **{status: sum(task.status == status for task in tasks)
           for status in ("pending", "in_progress", "done", "cancelled")},
        "overdue": sum(task.to_dict()["overdue"] for task in tasks),
    }
