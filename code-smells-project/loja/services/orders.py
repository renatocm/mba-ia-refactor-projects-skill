from decimal import Decimal

from loja.database import transaction
from loja.errors import DomainError
from loja.models import validation
from loja.models.repositories import Orders, Products, Users
from loja.services import policy


class OrderService:
    def __init__(self, db):
        self.db = db
        self.orders, self.products, self.users = Orders(db), Products(db), Users(db)

    def create(self, data, actor):
        user_id = validation.integer(data.get("usuario_id"), "Usuario ID")
        policy.owner_or_admin(actor, user_id)
        quantities = validation.order_items(data.get("itens"))
        with transaction(self.db):
            if self.users.get(user_id) is None:
                raise DomainError("Usuário não encontrado", 404)
            lines, total = [], Decimal("0")
            for product_id, quantity in quantities.items():
                product = self.products.get(product_id)
                if product is None or not product["ativo"]:
                    raise DomainError("Produto não encontrado ou inativo")
                if product["estoque"] < quantity:
                    raise DomainError("Estoque insuficiente")
                total += Decimal(str(product["preco"])) * quantity
                lines.append((product_id, quantity, product["preco"]))
            order_id = self.orders.create(user_id, float(total))
            for product_id, quantity, price in lines:
                if not self.products.debit(product_id, quantity):
                    raise DomainError("Estoque insuficiente")
                self.orders.add_item(order_id, product_id, quantity, price)
            return {"pedido_id": order_id, "total": float(total)}

    def list(self, page, limit, actor, user_id=None):
        if user_id is not None:
            validation.integer(user_id, "Usuario ID")
        if user_id is None:
            policy.admin(actor)
        else:
            policy.owner_or_admin(actor, user_id)
        # One read snapshot covers both batched queries.
        self.db.execute("BEGIN")
        try:
            result = self.orders.list(limit, (page - 1) * limit, user_id)
            self.db.commit()
            return result
        except BaseException:
            self.db.rollback()
            raise

    def update_status(self, id, data, actor):
        policy.admin(actor)
        validation.integer(id, "Pedido ID")
        status = data.get("status")
        if not isinstance(status, str) or status not in validation.TRANSITIONS:
            raise DomainError("Status inválido")
        with transaction(self.db):
            order = self.orders.get(id)
            if order is None:
                raise DomainError("Pedido não encontrado", 404)
            previous = order["status"]
            if previous == status:
                return  # Idempotent, including repeated cancellation.
            if status not in validation.TRANSITIONS[previous]:
                raise DomainError("Transição de status inválida", 409)
            if status == "cancelado":
                self.products.restore(id)
            self.orders.set_status(id, status)
