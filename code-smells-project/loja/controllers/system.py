from flask import g, jsonify

from loja.database import get_db
from loja.services.reports import ReportService
from loja.services.system import health


def index():
    return jsonify(mensagem="Bem-vindo à API da Loja", versao="1.0.0", endpoints={
        "produtos": "/produtos", "usuarios": "/usuarios", "pedidos": "/pedidos",
        "login": "/login", "relatorios": "/relatorios/vendas", "health": "/health"})


def health_check():
    return jsonify(health(get_db()))


def relatorio_vendas():
    return jsonify(dados=ReportService(get_db()).sales(g.actor), sucesso=True)
