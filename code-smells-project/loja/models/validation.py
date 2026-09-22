"""Shared input invariants, independent of Flask and persistence."""
import math
import re

from loja.errors import DomainError

CATEGORIES = {"informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"}
TRANSITIONS = {
    "pendente": {"aprovado", "cancelado"},
    "aprovado": {"enviado", "cancelado"},
    "enviado": {"entregue"},
    "entregue": set(),
    "cancelado": set(),
}


def text(value, field, minimum=1, maximum=200):
    if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum:
        raise DomainError(f"{field} inválido")
    return value.strip()


def integer(value, field, minimum=1, maximum=2147483647):
    if type(value) is not int or not minimum <= value <= maximum:
        raise DomainError(f"{field} deve ser inteiro entre {minimum} e {maximum}")
    return value


def number(value, field):
    if type(value) not in (int, float) or not 0 <= value <= 1000000000 or not math.isfinite(value):
        raise DomainError(f"{field} deve ser um número finito não negativo até 1000000000")
    return value


def product(data):
    result = {
        "nome": text(data.get("nome"), "Nome", 2),
        "descricao": text(data.get("descricao", ""), "Descrição", 0, 5000),
        "preco": number(data.get("preco"), "Preço"),
        "estoque": integer(data.get("estoque"), "Estoque", 0),
        "categoria": text(data.get("categoria", "geral"), "Categoria"),
    }
    if result["categoria"] not in CATEGORIES:
        raise DomainError("Categoria inválida")
    return result


def email(value):
    value = text(value, "Email", maximum=254).lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise DomainError("Email inválido")
    return value


def password(value, new=True):
    minimum = 8 if new else 1
    if not isinstance(value, str) or not minimum <= len(value) <= 1024:
        raise DomainError(f"Senha deve ter entre {minimum} e 1024 caracteres")
    return value


def order_items(items):
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise DomainError("Pedido deve ter entre 1 e 100 itens")
    quantities = {}
    for item in items:
        if not isinstance(item, dict):
            raise DomainError("Item inválido")
        product_id = integer(item.get("produto_id"), "Produto ID")
        quantity = integer(item.get("quantidade"), "Quantidade", maximum=1000000)
        quantities[product_id] = integer(quantities.get(product_id, 0) + quantity, "Quantidade", maximum=1000000)
    return quantities


def pagination(args):
    def parse(name, default, maximum):
        value = args.get(name, str(default))
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,10}", value):
            raise DomainError(f"{name} inválido")
        return integer(int(value), name, maximum=maximum)
    page, limit = parse("page", 1, 1000000), parse("per_page", 50, 100)
    return page, limit


def search(args):
    filters = {"termo": text(args.get("q", ""), "Busca", 0, 200), "categoria": None,
               "preco_min": None, "preco_max": None}
    if args.get("categoria"):
        filters["categoria"] = text(args["categoria"], "Categoria")
    for field in ("preco_min", "preco_max"):
        if args.get(field) not in (None, ""):
            try:
                value = float(args[field])
            except (ValueError, TypeError):
                raise DomainError(f"{field} inválido") from None
            filters[field] = number(value, field)
    if filters["preco_min"] is not None and filters["preco_max"] is not None and filters["preco_min"] > filters["preco_max"]:
        raise DomainError("Preço mínimo deve ser menor ou igual ao máximo")
    return filters
