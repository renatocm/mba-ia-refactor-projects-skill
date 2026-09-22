from loja.models.repositories import check_health


def health(db):
    check_health(db)
    return {"status": "ok", "database": "connected", "versao": "1.0.0"}
