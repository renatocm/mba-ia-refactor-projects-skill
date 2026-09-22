from flask import g, jsonify

from loja import presenters
from loja.controllers import body, page, paginated
from loja.database import get_db
from loja.services.orders import OrderService


def criar_pedido():
    result = OrderService(get_db()).create(body(), g.actor)
    return jsonify(dados=result, sucesso=True, mensagem="Pedido criado com sucesso"), 201


def _list(user_id=None):
    number, limit = page()
    rows, items = OrderService(get_db()).list(number, limit, g.actor, user_id)
    return jsonify(paginated(presenters.orders(rows, items), number, limit))


def listar_todos_pedidos():
    return _list()


def listar_pedidos_usuario(usuario_id):
    return _list(usuario_id)


def atualizar_status_pedido(pedido_id):
    OrderService(get_db()).update_status(pedido_id, body(), g.actor)
    return jsonify(sucesso=True, mensagem="Status atualizado")
