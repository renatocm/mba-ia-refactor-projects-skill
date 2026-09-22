from uuid import uuid4

from flask import current_app, jsonify
from werkzeug.exceptions import HTTPException


class DomainError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def register_errors(app):
    @app.errorhandler(DomainError)
    def domain_error(error):
        response = jsonify(erro=error.message, sucesso=False)
        if error.status == 401:
            response.headers["WWW-Authenticate"] = "Bearer"
        return response, error.status

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {400: "JSON ou requisição inválida", 404: "Recurso não encontrado",
                    405: "Método não permitido", 413: "Corpo da requisição muito grande",
                    415: "Envie Content-Type application/json"}
        response = error.get_response()
        response.data = current_app.json.dumps({"erro": messages.get(error.code, "Requisição inválida"), "sucesso": False})
        response.content_type = "application/json"
        return response

    @app.errorhandler(Exception)
    def unexpected_error(error):
        reference = uuid4().hex
        # Do not log exception messages, SQL, request bodies or authentication headers.
        current_app.logger.error("Falha interna ref=%s tipo=%s", reference, type(error).__name__)
        return jsonify(erro="Erro interno", sucesso=False, referencia=reference), 500
