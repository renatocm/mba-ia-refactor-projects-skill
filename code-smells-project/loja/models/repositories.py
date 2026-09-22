"""Parameterized data access; callers own transaction boundaries."""
def check_health(db):
    db.execute("SELECT 1")


class Products:
    def __init__(self, db):
        self.db = db

    def get(self, id):
        return self.db.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()

    def list(self, limit, offset, termo="", categoria=None, preco_min=None, preco_max=None):
        clauses, values = [], []
        if termo:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            values.extend([f"%{termo}%", f"%{termo}%"])
        if categoria:
            clauses.append("categoria = ?")
            values.append(categoria)
        if preco_min is not None:
            clauses.append("preco >= ?")
            values.append(preco_min)
        if preco_max is not None:
            clauses.append("preco <= ?")
            values.append(preco_max)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        return self.db.execute("SELECT * FROM produtos" + where + " ORDER BY id LIMIT ? OFFSET ?", (*values, limit, offset)).fetchall()

    def create(self, data):
        return self.db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            tuple(data[k] for k in ("nome", "descricao", "preco", "estoque", "categoria")),
        ).lastrowid

    def update(self, id, data):
        self.db.execute("UPDATE produtos SET nome=?, descricao=?, preco=?, estoque=?, categoria=? WHERE id=?",
                        (*[data[k] for k in ("nome", "descricao", "preco", "estoque", "categoria")], id))

    def referenced(self, id):
        return self.db.execute("SELECT 1 FROM itens_pedido WHERE produto_id=? LIMIT 1", (id,)).fetchone() is not None

    def delete(self, id):
        self.db.execute("DELETE FROM produtos WHERE id=?", (id,))

    def debit(self, id, quantity):
        return self.db.execute("UPDATE produtos SET estoque=estoque-? WHERE id=? AND ativo=1 AND estoque>=?",
                               (quantity, id, quantity)).rowcount == 1

    def restore(self, order_id):
        self.db.execute("""UPDATE produtos SET estoque=estoque + (
            SELECT SUM(quantidade) FROM itens_pedido WHERE pedido_id=? AND produto_id=produtos.id
        ) WHERE id IN (SELECT produto_id FROM itens_pedido WHERE pedido_id=?)""", (order_id, order_id))


class Users:
    def __init__(self, db):
        self.db = db

    def get(self, id):
        return self.db.execute("SELECT * FROM usuarios WHERE id=?", (id,)).fetchone()

    def by_email(self, email):
        return self.db.execute("SELECT * FROM usuarios WHERE email=?", (email,)).fetchone()

    def list(self, limit, offset):
        return self.db.execute("SELECT * FROM usuarios ORDER BY id LIMIT ? OFFSET ?", (limit, offset)).fetchall()

    def create(self, name, email, password_hash, role):
        return self.db.execute("INSERT INTO usuarios (nome,email,senha_hash,tipo) VALUES (?,?,?,?)",
                               (name, email, password_hash, role)).lastrowid


class Orders:
    def __init__(self, db):
        self.db = db

    def get(self, id):
        return self.db.execute("SELECT * FROM pedidos WHERE id=?", (id,)).fetchone()

    def create(self, user_id, total):
        return self.db.execute("INSERT INTO pedidos (usuario_id,total) VALUES (?,?)", (user_id, total)).lastrowid

    def add_item(self, order_id, product_id, quantity, price):
        self.db.execute("INSERT INTO itens_pedido (pedido_id,produto_id,quantidade,preco_unitario) VALUES (?,?,?,?)",
                        (order_id, product_id, quantity, price))

    def set_status(self, id, status):
        self.db.execute("UPDATE pedidos SET status=? WHERE id=?", (status, id))

    def list(self, limit, offset, user_id=None):
        where, values = (" WHERE usuario_id=?", [user_id]) if user_id is not None else ("", [])
        rows = self.db.execute("SELECT * FROM pedidos" + where + " ORDER BY id LIMIT ? OFFSET ?",
                               (*values, limit, offset)).fetchall()
        if not rows:
            return rows, []
        # Only placeholder count is generated, never external SQL identifiers or values.
        placeholders = ",".join("?" for _ in rows)
        items = self.db.execute("""SELECT i.pedido_id,i.produto_id,p.nome AS produto_nome,
            i.quantidade,i.preco_unitario FROM itens_pedido i JOIN produtos p ON p.id=i.produto_id
            WHERE i.pedido_id IN (""" + placeholders + ") ORDER BY i.pedido_id,i.id",
                                tuple(row["id"] for row in rows)).fetchall()
        return rows, items

    def sales(self):
        return self.db.execute("""SELECT COUNT(*) AS total_pedidos, COALESCE(SUM(total),0) AS faturamento,
            COALESCE(SUM(status='pendente'),0) AS pendentes,
            COALESCE(SUM(status='aprovado'),0) AS aprovados,
            COALESCE(SUM(status='cancelado'),0) AS cancelados FROM pedidos""").fetchone()
