import secrets

from itsdangerous import BadData, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from loja.database import transaction
from loja.errors import DomainError
from loja.models import validation
from loja.models.repositories import Users
from loja.services import policy


class UserService:
    def __init__(self, db):
        self.db, self.users = db, Users(db)

    def create(self, data, role="cliente"):
        name = validation.text(data.get("nome"), "Nome", 2)
        email = validation.email(data.get("email"))
        password = validation.password(data.get("senha"))
        # The role argument is supplied only by trusted composition/CLI code.
        if role not in ("admin", "cliente"):
            raise DomainError("Tipo inválido")
        password_hash = generate_password_hash(password, method="scrypt")
        with transaction(self.db):
            if self.users.by_email(email):
                raise DomainError("Email já cadastrado", 409)
            return self.users.create(name, email, password_hash, role)

    def get(self, id, actor):
        validation.integer(id, "Usuario ID")
        policy.owner_or_admin(actor, id)
        row = self.users.get(id)
        if row is None:
            raise DomainError("Usuário não encontrado", 404)
        return row

    def list(self, page, limit, actor):
        policy.admin(actor)
        return self.users.list(limit, (page - 1) * limit)


class TokenAuth:
    def __init__(self, secret, ttl):
        self.serializer = URLSafeTimedSerializer(secret, salt="loja-access-token-v1")
        self.ttl = ttl
        self.dummy_hash = generate_password_hash(secrets.token_urlsafe(32), method="scrypt")

    def login(self, data, users):
        email = validation.email(data.get("email"))
        password = validation.password(data.get("senha"), new=False)
        user = users.by_email(email)
        valid = check_password_hash(user["senha_hash"] if user else self.dummy_hash, password)
        if not user or not valid:
            raise DomainError("Email ou senha inválidos", 401)
        token = self.serializer.dumps({"uid": user["id"]})
        return user, token

    def authenticate(self, token, users):
        try:
            data = self.serializer.loads(token, max_age=self.ttl)
        except BadData:
            raise DomainError("Token inválido ou expirado", 401) from None
        if not isinstance(data, dict) or type(data.get("uid")) is not int:
            raise DomainError("Token inválido", 401)
        user = users.get(data["uid"])
        if user is None:
            raise DomainError("Token inválido", 401)
        return user
