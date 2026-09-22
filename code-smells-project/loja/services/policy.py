from loja.errors import DomainError


def admin(actor):
    if actor["tipo"] != "admin":
        raise DomainError("Acesso não permitido", 403)


def owner_or_admin(actor, user_id):
    if actor["tipo"] != "admin" and actor["id"] != user_id:
        raise DomainError("Acesso não permitido", 403)
