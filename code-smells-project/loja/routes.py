"""HTTP method/path bindings and access policy; JSON views live in presenters."""
from flask import Blueprint

from loja.auth import protected
from loja.controllers import orders, products, system, users


def blueprint():
    routes = Blueprint("api", __name__)
    definitions = [
        ("/", "GET", system.index, "public"),
        ("/health", "GET", system.health_check, "public"),
        ("/produtos", "GET", products.listar_produtos, "public"),
        ("/produtos/busca", "GET", products.buscar_produtos, "public"),
        ("/produtos/<int:id>", "GET", products.buscar_produto, "public"),
        ("/produtos", "POST", products.criar_produto, "admin"),
        ("/produtos/<int:id>", "PUT", products.atualizar_produto, "admin"),
        ("/produtos/<int:id>", "DELETE", products.deletar_produto, "admin"),
        ("/usuarios", "GET", users.listar_usuarios, "admin"),
        ("/usuarios/<int:id>", "GET", users.buscar_usuario, "authenticated"),
        ("/usuarios", "POST", users.criar_usuario, "public"),
        ("/login", "POST", users.login, "public"),
        ("/pedidos", "POST", orders.criar_pedido, "authenticated"),
        ("/pedidos", "GET", orders.listar_todos_pedidos, "admin"),
        ("/pedidos/usuario/<int:usuario_id>", "GET", orders.listar_pedidos_usuario, "authenticated"),
        ("/pedidos/<int:pedido_id>/status", "PUT", orders.atualizar_status_pedido, "admin"),
        ("/relatorios/vendas", "GET", system.relatorio_vendas, "admin"),
    ]
    for path, method, controller, access in definitions:
        view = controller if access == "public" else protected(controller, admin=access == "admin")
        routes.add_url_rule(path, controller.__name__, view, methods=[method])
    return routes
