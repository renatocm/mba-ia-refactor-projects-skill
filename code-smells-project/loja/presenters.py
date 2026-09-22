"""Explicit public DTOs; password/hash never enter a response."""
PRODUCT_FIELDS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")
USER_FIELDS = ("id", "nome", "email", "tipo", "criado_em")
ORDER_FIELDS = ("id", "usuario_id", "status", "total", "criado_em")
ITEM_FIELDS = ("produto_id", "produto_nome", "quantidade", "preco_unitario")


def product(row):
    return {field: row[field] for field in PRODUCT_FIELDS}


def user(row, login=False):
    fields = USER_FIELDS[:-1] if login else USER_FIELDS
    return {field: row[field] for field in fields}


def orders(rows, items):
    result = {row["id"]: {**{field: row[field] for field in ORDER_FIELDS}, "itens": []} for row in rows}
    for item in items:
        result[item["pedido_id"]]["itens"].append({field: item[field] for field in ITEM_FIELDS})
    return list(result.values())
