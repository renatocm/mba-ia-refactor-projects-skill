from flask import jsonify
from sqlalchemy.exc import IntegrityError
from services.exceptions import ApplicationError, InvalidInput, NotFound, Conflict, AccessDenied, InvalidCredentials

def register_error_handlers(app):
    @app.errorhandler(ApplicationError)
    def application_error(error):
        status = {InvalidInput: 400, NotFound: 404, Conflict: 409,
                  AccessDenied: 403, InvalidCredentials: 401}[type(error)]
        return jsonify(error=str(error)), status
    @app.errorhandler(400)
    def bad_request(error): return jsonify(error="Dados inválidos"), 400
    @app.errorhandler(404)
    def not_found(error): return jsonify(error="Recurso não encontrado"), 404
    @app.errorhandler(405)
    def method_not_allowed(error): return jsonify(error="Método não permitido"), 405
    @app.errorhandler(IntegrityError)
    def integrity_error(error): return jsonify(error="Operação viola a integridade dos dados"), 409
    @app.errorhandler(Exception)
    def internal_error(error):
        app.logger.exception("Unhandled application error")
        return jsonify(error="Erro interno"), 500
