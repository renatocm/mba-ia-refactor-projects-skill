"""Category queries and transactional mutations."""
from sqlalchemy import func
from database import db
from models.category import Category
from models.task import Task
from services.exceptions import NotFound
from services.transactions import transactional
from utils.validation import validate_category


def require_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        raise NotFound("Categoria não encontrada")
    return category


def list_categories():
    rows = (db.session.query(Category, func.count(Task.id))
            .outerjoin(Task).group_by(Category.id).all())
    return [{**category.to_dict(), "task_count": count} for category, count in rows]


@transactional
def create(data):
    validate_category(data)
    category = Category(name=data["name"], description=data.get("description", ""),
                        color=data.get("color", "#000000"))
    db.session.add(category)
    db.session.flush()
    db.session.refresh(category)
    return category.to_dict()


@transactional
def update(category_id, data):
    category = require_category(category_id)
    validate_category(data, True)
    for key in ("name", "description", "color"):
        if key in data:
            setattr(category, key, data[key])
    db.session.flush()
    db.session.refresh(category)
    return category.to_dict()


@transactional
def delete(category_id):
    db.session.delete(require_category(category_id))
