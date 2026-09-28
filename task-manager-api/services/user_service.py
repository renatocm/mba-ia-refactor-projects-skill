from database import db
from models.user import User
from utils.validation import validate_user, require_data
from models.task import Task
from sqlalchemy.orm import selectinload
from services.exceptions import NotFound, AccessDenied, InvalidCredentials, InvalidInput, Conflict
from services.transactions import transactional
def require_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFound("Usuário não encontrado")
    return user

def get(user_id):
    user = require_user(user_id)
    return {**user.to_dict(), "tasks": [task.to_dict() for task in user.tasks]}

def list_users():
    users = User.query.options(selectinload(User.tasks)).all()
    return [{**user.to_dict(), "task_count": len(user.tasks)} for user in users]
@transactional
def create(data):
    require_data(data)
    data = {key: value for key, value in data.items() if key not in {"role", "active"}}
    validate_user(data)
    if User.query.filter_by(email=data["email"]).first(): raise Conflict(str(KeyError("Email já cadastrado")))
    if "password" not in data:
        raise InvalidInput("Senha é obrigatória")
    user=User(name=data["name"].strip(),email=data["email"].lower(),role=data.get("role","user")); user.set_password(data["password"]); db.session.add(user); db.session.flush(); db.session.refresh(user); return user.to_dict()
@transactional
def update(user_id,data,actor):
    user = require_user(user_id)
    if actor.id != user_id and actor.role != "admin":
        raise AccessDenied("Acesso negado")
    require_data(data)
    if ("role" in data or "active" in data) and actor.role != "admin":
        raise AccessDenied("Acesso negado")
    validate_user(data,True)
    for key in ("name","email","role","active"):
        if key in data: setattr(user,key,data[key])
    if "password" in data: user.set_password(data["password"])
    db.session.flush(); db.session.refresh(user); return user.to_dict()


@transactional
def delete(user_id):
    db.session.delete(require_user(user_id))


def tasks(user_id):
    require_user(user_id)
    return [task.to_dict() for task in Task.query.filter_by(user_id=user_id).all()]


def authenticate(data):
    if not isinstance(data, dict):
        raise InvalidInput("Dados inválidos")
    email, password = data.get("email", ""), data.get("password", "")
    if not isinstance(email, str) or not isinstance(password, str):
        raise InvalidInput("Dados inválidos")
    user = User.query.filter_by(email=email.lower()).first()
    if not user or not user.check_password(password):
        raise InvalidCredentials("Credenciais inválidas")
    if not user.active:
        raise AccessDenied("Usuário inativo")
    return user
