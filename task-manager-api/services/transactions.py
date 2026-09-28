"""One commit per mutating use case; failures always roll back."""
from functools import wraps
from database import db
from services.exceptions import InvalidInput


def transactional(operation):
    @wraps(operation)
    def wrapped(*args, **kwargs):
        try:
            result = operation(*args, **kwargs)
            db.session.commit()
            return result
        except ValueError as error:
            db.session.rollback()
            raise InvalidInput(str(error)) from error
        except TypeError as error:
            db.session.rollback()
            raise InvalidInput("Dados inválidos") from error
        except Exception:
            db.session.rollback()
            raise
    return wrapped
