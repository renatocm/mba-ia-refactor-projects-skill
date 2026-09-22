from functools import wraps

from flask import current_app, g, request

from loja.database import get_db
from loja.errors import DomainError
from loja.models.repositories import Users
from loja.services import policy


def protected(view, admin=False):
    @wraps(view)
    def wrapped(*args, **kwargs):
        parts = request.headers.get("Authorization", "").split()
        if len(parts) != 2 or parts[0].lower() != "bearer" or len(parts[1]) > 4096:
            raise DomainError("Autenticação necessária", 401)
        g.actor = current_app.extensions["token_auth"].authenticate(parts[1], Users(get_db()))
        if admin:
            policy.admin(g.actor)
        return view(*args, **kwargs)
    return wrapped
