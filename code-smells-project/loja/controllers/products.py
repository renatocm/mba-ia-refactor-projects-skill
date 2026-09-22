from flask import g, jsonify, request

from loja import presenters
from loja.controllers import body, page, paginated
from loja.database import get_db
from loja.models.validation import search
from loja.services.products import ProductService


def listar_produtos():
    number, limit = page()
    rows = ProductService(get_db()).list(number, limit)
    return jsonify(paginated([presenters.product(row) for row in rows], number, limit))


def buscar_produtos():
    number, limit = page()
    rows = ProductService(get_db()).list(number, limit, **search(request.args))
    return jsonify(**paginated([presenters.product(row) for row in rows], number, limit), total=len(rows))


def buscar_produto(id):
    return jsonify(dados=presenters.product(ProductService(get_db()).get(id)), sucesso=True)


def criar_produto():
    id = ProductService(get_db()).create(body(), g.actor)
    return jsonify(dados={"id": id}, sucesso=True, mensagem="Produto criado"), 201


def atualizar_produto(id):
    ProductService(get_db()).update(id, body(), g.actor)
    return jsonify(sucesso=True, mensagem="Produto atualizado")


def deletar_produto(id):
    ProductService(get_db()).delete(id, g.actor)
    return jsonify(sucesso=True, mensagem="Produto deletado")
