from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.validation import validate_task
from utils.time import parse_date,utc_now
from sqlalchemy.orm import joinedload

def list_tasks(): return Task.query.options(joinedload(Task.user),joinedload(Task.category)).all()
def get_task(task_id): return db.session.get(Task,task_id)
def create(data):
    validate_task(data); task=Task(title=data["title"].strip(),description=data.get("description",""),status=data.get("status","pending"),priority=data.get("priority",3),user_id=data.get("user_id"),category_id=data.get("category_id"),tags=",".join(data.get("tags",[])))
    if data.get("due_date"): task.due_date=parse_date(data["due_date"])
    if task.user_id and not db.session.get(User,task.user_id): raise LookupError("Usuário não encontrado")
    if task.category_id and not db.session.get(Category,task.category_id): raise LookupError("Categoria não encontrada")
    db.session.add(task); db.session.commit(); return task
def update(task,data):
    validate_task(data,True)
    if data.get("user_id") and not db.session.get(User,data["user_id"]): raise LookupError("Usuário não encontrado")
    if data.get("category_id") and not db.session.get(Category,data["category_id"]): raise LookupError("Categoria não encontrada")
    for key in ("title","description","status","priority","user_id","category_id"):
        if key in data: setattr(task,key,data[key])
    if "tags" in data: task.tags=",".join(data["tags"] or [])
    if "due_date" in data: task.due_date=parse_date(data["due_date"]) if data["due_date"] else None
    task.updated_at=utc_now(); db.session.commit(); return task
