from flask import current_app, g, jsonify

from loja import presenters
from loja.controllers import body, page, paginated
from loja.database import get_db
from loja.models.repositories import Users
from loja.services.users import UserService


def listar_usuarios():
    number, limit = page()
    rows = UserService(get_db()).list(number, limit, g.actor)
    return jsonify(paginated([presenters.user(row) for row in rows], number, limit))


def buscar_usuario(id):
    return jsonify(dados=presenters.user(UserService(get_db()).get(id, g.actor)), sucesso=True)


def criar_usuario():
    id = UserService(get_db()).create(body())
    return jsonify(dados={"id": id}, sucesso=True), 201


def login():
    auth = current_app.extensions["token_auth"]
    user, token = auth.login(body(), Users(get_db()))
    response = jsonify(dados=presenters.user(user, login=True), sucesso=True, mensagem="Login OK",
                       token=token, token_type="Bearer", expires_in=auth.ttl)
    response.headers["Cache-Control"] = "no-store"
    return response
