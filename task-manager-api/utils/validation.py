import re
from utils.time import parse_date
VALID_STATUSES = {"pending", "in_progress", "done", "cancelled"}
VALID_ROLES = {"user", "admin", "manager"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def require_data(data):
    if not isinstance(data, dict): raise ValueError("Dados inválidos")

def validate_task(data, partial=False):
    require_data(data)
    if not partial or "title" in data:
        title=data.get("title")
        if not isinstance(title,str) or not 3 <= len(title.strip()) <= 200: raise ValueError("Título deve ter entre 3 e 200 caracteres")
    if "status" in data and data["status"] not in VALID_STATUSES: raise ValueError("Status inválido")
    if "priority" in data and (not isinstance(data["priority"],int) or isinstance(data["priority"],bool) or not 1 <= data["priority"] <= 5): raise ValueError("Prioridade deve ser entre 1 e 5")
    if "tags" in data and data["tags"] is not None and (not isinstance(data["tags"],list) or not all(isinstance(x,str) for x in data["tags"])): raise ValueError("Tags devem ser uma lista de textos")
    if data.get("due_date"): parse_date(data["due_date"])

def validate_user(data, partial=False):
    require_data(data)
    if not partial or "name" in data:
        if not isinstance(data.get("name"),str) or not data["name"].strip(): raise ValueError("Nome é obrigatório")
    if not partial or "email" in data:
        if not isinstance(data.get("email"),str) or not EMAIL_RE.match(data["email"]): raise ValueError("Email inválido")
    if "password" in data and (not isinstance(data["password"],str) or len(data["password"]) < 8): raise ValueError("Senha deve ter no mínimo 8 caracteres")
    if "role" in data and data["role"] not in VALID_ROLES: raise ValueError("Role inválido")

def validate_category(data, partial=False):
    require_data(data)
    if not partial or "name" in data:
        if not isinstance(data.get("name"),str) or not data["name"].strip(): raise ValueError("Nome é obrigatório")
    if "color" in data and (not isinstance(data["color"],str) or not re.match(r"^#[0-9a-fA-F]{6}$",data["color"])): raise ValueError("Cor inválida")
