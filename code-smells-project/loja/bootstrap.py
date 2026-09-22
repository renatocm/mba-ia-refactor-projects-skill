"""Explicit, non-destructive initialization and legacy migration."""
from pathlib import Path
import sqlite3

from werkzeug.security import generate_password_hash

from loja.database import connect, transaction

SCHEMA = Path(__file__).parent / "models" / "schema.sql"


def initialize(path):
    path = Path(path)
    # Exclusive creation prevents accidental reset of any existing database/file.
    with path.open("xb"):
        pass
    db = None
    try:
        db = connect(path)
        db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA.read_text() + "\nCOMMIT;")
    except BaseException:
        if db is not None:
            db.close()
            db = None
        path.unlink()
        raise
    finally:
        if db is not None:
            db.close()


def migrate_legacy(source, destination):
    """Copy to a NEW file. Source is read-only; invalid data aborts, never discarded."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file():
        raise ValueError("Banco de origem não encontrado")
    old = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
    old.row_factory = sqlite3.Row
    new = None
    created = False
    try:
        old.execute("BEGIN")  # Consistent source snapshot across all tables.
        if old.execute("PRAGMA user_version").fetchone()[0] != 0:
            raise ValueError("A origem não é um banco legado versão 0")
        initialize(destination)
        created = True
        new = connect(destination)
        with transaction(new):
            for row in old.execute("SELECT * FROM usuarios ORDER BY id"):
                if not isinstance(row["senha"], str) or not row["senha"]:
                    raise ValueError("Senha legada inválida; resolva os dados antes de migrar")
                new.execute("INSERT INTO usuarios (id,nome,email,senha_hash,tipo,criado_em) VALUES (?,?,?,?,?,?)",
                            (row["id"], row["nome"], row["email"].strip().lower(),
                             generate_password_hash(row["senha"], method="scrypt"), row["tipo"], row["criado_em"]))
            for table, columns in (
                ("produtos", ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")),
                ("pedidos", ("id", "usuario_id", "status", "total", "criado_em")),
                ("itens_pedido", ("id", "pedido_id", "produto_id", "quantidade", "preco_unitario")),
            ):
                # Identifiers are internal constants, not external input.
                for row in old.execute(f"SELECT * FROM {table} ORDER BY id"):
                    new.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                                tuple(row[key] for key in columns))
            # Preserve AUTOINCREMENT high-water marks, including deleted IDs.
            for table in ("usuarios", "produtos", "pedidos", "itens_pedido"):
                sequence = old.execute("SELECT seq FROM sqlite_sequence WHERE name=?", (table,)).fetchone()
                if sequence:
                    if new.execute("SELECT 1 FROM sqlite_sequence WHERE name=?", (table,)).fetchone():
                        new.execute("UPDATE sqlite_sequence SET seq=MAX(seq,?) WHERE name=?", (sequence[0], table))
                    else:
                        new.execute("INSERT INTO sqlite_sequence(name,seq) VALUES (?,?)", (table, sequence[0]))
    except BaseException:
        if new is not None:
            new.close()
            new = None
        if created:
            destination.unlink()
        raise
    finally:
        if new is not None:
            new.close()
        old.close()
