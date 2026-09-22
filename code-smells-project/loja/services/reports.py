from loja.models.repositories import Orders
from loja.services import policy

DISCOUNT_TIERS = ((10000, 0.1), (5000, 0.05), (1000, 0.02))


class ReportService:
    def __init__(self, db):
        self.orders = Orders(db)

    def sales(self, actor):
        policy.admin(actor)
        row = self.orders.sales()
        count, revenue = row["total_pedidos"], row["faturamento"]
        discount = next((revenue * rate for threshold, rate in DISCOUNT_TIERS if revenue > threshold), 0)
        # Preserve the audited definition: revenue includes every order status.
        return {"total_pedidos": count, "faturamento_bruto": round(revenue, 2),
                "desconto_aplicavel": round(discount, 2), "faturamento_liquido": round(revenue - discount, 2),
                "pedidos_pendentes": row["pendentes"], "pedidos_aprovados": row["aprovados"],
                "pedidos_cancelados": row["cancelados"], "ticket_medio": round(revenue / count, 2) if count else 0}
