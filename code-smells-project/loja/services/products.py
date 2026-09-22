from loja.database import transaction
from loja.errors import DomainError
from loja.models import validation
from loja.models.repositories import Products
from loja.services import policy


class ProductService:
    def __init__(self, db):
        self.db, self.products = db, Products(db)

    def get(self, id):
        validation.integer(id, "Produto ID")
        row = self.products.get(id)
        if row is None:
            raise DomainError("Produto não encontrado", 404)
        return row

    def list(self, page, limit, **filters):
        return self.products.list(limit, (page - 1) * limit, **filters)

    def create(self, data, actor):
        policy.admin(actor)
        data = validation.product(data)
        with transaction(self.db):
            return self.products.create(data)

    def update(self, id, data, actor):
        policy.admin(actor)
        data = validation.product(data)
        with transaction(self.db):
            self.get(id)
            self.products.update(id, data)

    def delete(self, id, actor):
        policy.admin(actor)
        with transaction(self.db):
            self.get(id)
            if self.products.referenced(id):
                raise DomainError("Produto referenciado por pedidos não pode ser excluído", 409)
            self.products.delete(id)
