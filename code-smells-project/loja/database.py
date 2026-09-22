"""Request-local connection and explicit units of work. No DDL or seed on access."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import current_app, g

from loja.errors import DomainError


def connect(path):
    db = sqlite3.connect(str(path), isolation_level=None, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def get_db():
    if "db" not in g:
        path = Path(current_app.config["DATABASE"])
        if not path.is_file():
            raise DomainError("Banco não inicializado; execute init-db", 503)
        db = connect(path)
        if db.execute("PRAGMA user_version").fetchone()[0] != 1:
            db.close()
            raise DomainError("Banco requer migração; consulte a documentação", 503)
        g.db = db
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        try:
            if db.in_transaction:
                db.rollback()
        finally:
            db.close()


@contextmanager
def transaction(db):
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
