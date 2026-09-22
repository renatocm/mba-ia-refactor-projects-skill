from flask import request

from loja.errors import DomainError
from loja.models.validation import pagination


def body():
    data = request.get_json()
    if not isinstance(data, dict):
        raise DomainError("O corpo JSON deve ser um objeto")
    return data


def page():
    return pagination(request.args)


def paginated(data, page_number, limit):
    return {"dados": data, "sucesso": True, "page": page_number, "per_page": limit}
