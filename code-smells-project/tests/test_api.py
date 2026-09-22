import concurrent.futures
import json
import secrets
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import check_password_hash, generate_password_hash

from loja import create_app
from loja.bootstrap import initialize, migrate_legacy
from loja.database import connect, get_db
from loja.models.repositories import Orders


class APITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = "senha-de-teste-segura"
        cls.password_hash = generate_password_hash(cls.password, method="scrypt")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.db"
        initialize(self.path)
        self.app = create_app({"TESTING": True, "SECRET_KEY": secrets.token_hex(32), "DATABASE": str(self.path)})
        self.client = self.app.test_client()
        with self.db() as db:
            for id, role in ((1, "admin"), (2, "cliente"), (3, "cliente")):
                db.execute("INSERT INTO usuarios(id,nome,email,senha_hash,tipo) VALUES (?,?,?,?,?)",
                           (id, f"Pessoa {id}", f"pessoa{id}@example.test", self.password_hash, role))
            db.execute("INSERT INTO produtos(id,nome,descricao,preco,estoque,categoria) VALUES (1,'Produto de teste','',10,10,'geral')")
        auth = self.app.extensions["token_auth"]
        self.admin = {"Authorization": "Bearer " + auth.serializer.dumps({"uid": 1})}
        self.user = {"Authorization": "Bearer " + auth.serializer.dumps({"uid": 2})}
        self.other = {"Authorization": "Bearer " + auth.serializer.dumps({"uid": 3})}
        self.product = {"nome": "Produto novo", "preco": 15.5, "estoque": 4}

    def db(self):
        db = connect(self.path)
        self.addCleanup(db.close)
        return db

    def order(self, quantity=2, headers=None, items=None):
        return self.client.post("/pedidos", headers=headers or self.user, json={
            "usuario_id": 2, "itens": items if items is not None else [{"produto_id": 1, "quantidade": quantity}]})

    def status(self, id, status, headers=None):
        return self.client.put(f"/pedidos/{id}/status", headers=headers or self.admin, json={"status": status})

    def test_all_existing_endpoints_success(self):
        for path in ("/", "/health", "/produtos", "/produtos/busca?q=teste", "/produtos/1"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        created = self.client.post("/produtos", headers=self.admin, json=self.product)
        self.assertEqual(created.status_code, 201)
        product_id = created.json["dados"]["id"]
        self.assertEqual(self.client.put(f"/produtos/{product_id}", headers=self.admin, json=self.product).status_code, 200)
        self.assertEqual(self.client.delete(f"/produtos/{product_id}", headers=self.admin).status_code, 200)
        created = self.client.post("/usuarios", json={"nome": "Nova Pessoa", "email": "nova@example.test", "senha": self.password})
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.get("/usuarios", headers=self.admin).status_code, 200)
        self.assertEqual(self.client.get("/usuarios/2", headers=self.user).status_code, 200)
        self.assertEqual(self.client.post("/login", json={"email": "pessoa2@example.test", "senha": self.password}).status_code, 200)
        order = self.order()
        self.assertEqual(order.status_code, 201)
        id = order.json["dados"]["pedido_id"]
        for path, headers in (("/pedidos", self.admin), ("/pedidos/usuario/2", self.user), ("/relatorios/vendas", self.admin)):
            self.assertEqual(self.client.get(path, headers=headers).status_code, 200)
        self.assertEqual(self.status(id, "aprovado").status_code, 200)
        for path in ("/admin/query", "/admin/reset-db"):
            for headers in ({}, self.admin):
                self.assertEqual(self.client.post(path, headers=headers, json={"sql": "DELETE FROM produtos"}).status_code, 404)
        self.assertEqual(self.db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0], 1)

    def test_anonymous_and_customer_access_matrix(self):
        admin_routes = [("post", "/produtos"), ("put", "/produtos/1"), ("delete", "/produtos/1"),
                        ("get", "/usuarios"), ("get", "/pedidos"), ("put", "/pedidos/1/status"), ("get", "/relatorios/vendas")]
        for method, path in admin_routes:
            with self.subTest(method=method, path=path):
                self.assertEqual(getattr(self.client, method)(path, json={}).status_code, 401)
                self.assertEqual(getattr(self.client, method)(path, headers=self.user, json={}).status_code, 403)
        for method, path in [("get", "/usuarios/2"), ("get", "/pedidos/usuario/2"), ("post", "/pedidos")]:
            self.assertEqual(getattr(self.client, method)(path, json={}).status_code, 401)
        self.assertEqual(self.client.get("/usuarios/2", headers=self.other).status_code, 403)
        self.assertEqual(self.client.get("/pedidos/usuario/2", headers=self.other).status_code, 403)
        self.assertEqual(self.order(headers=self.other).status_code, 403)

    def test_login_password_hash_and_public_dto(self):
        response = self.client.post("/usuarios", json={"nome": "Pessoa nova", "email": "NOVA@example.test", "senha": self.password, "tipo": "admin"})
        self.assertEqual(response.status_code, 201)
        row = self.db().execute("SELECT * FROM usuarios WHERE id=?", (response.json["dados"]["id"],)).fetchone()
        self.assertNotEqual(row["senha_hash"], self.password_hash)
        self.assertTrue(check_password_hash(row["senha_hash"], self.password))
        self.assertEqual(row["tipo"], "cliente")
        login = self.client.post("/login", json={"email": "nova@example.test", "senha": self.password})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.headers["Cache-Control"], "no-store")
        self.assertEqual(self.client.get(f'/usuarios/{row["id"]}', headers={"Authorization": "Bearer " + login.json["token"]}).status_code, 200)
        for path in ("/usuarios", "/usuarios/1", "/health"):
            payload = self.client.get(path, headers=self.admin).get_data(as_text=True)
            for secret in ("senha", "secret_key", "db_path", self.password, self.app.config["SECRET_KEY"]):
                self.assertNotIn(secret, payload)
        for email, password in (("nova@example.test", "errada"), ("ausente@example.test", self.password), ("nova@example.test'OR'1'='1", "errada")):
            self.assertEqual(self.client.post("/login", json={"email": email, "senha": password}).status_code, 401)

    def test_bad_expired_deleted_and_role_changed_tokens(self):
        auth = self.app.extensions["token_auth"]
        for token in ("invalid", self.user["Authorization"].split()[1] + "changed", auth.serializer.dumps([2]), auth.serializer.dumps({"uid": True})):
            self.assertEqual(self.client.get("/usuarios/2", headers={"Authorization": "Bearer " + token}).status_code, 401)
        with patch("itsdangerous.timed.time.time", return_value=1):
            expired = auth.serializer.dumps({"uid": 2})
        self.assertEqual(self.client.get("/usuarios/2", headers={"Authorization": "Bearer " + expired}).status_code, 401)
        self.db().execute("DELETE FROM usuarios WHERE id=3")
        self.assertEqual(self.client.get("/usuarios/3", headers=self.other).status_code, 401)
        self.db().execute("UPDATE usuarios SET tipo='cliente' WHERE id=1")
        self.assertEqual(self.client.get("/usuarios", headers=self.admin).status_code, 403)

    def test_injection_is_data(self):
        attack = "Caneca d'água'); DROP TABLE produtos; --"
        product = {**self.product, "nome": attack, "descricao": attack}
        created = self.client.post("/produtos", headers=self.admin, json=product)
        self.assertEqual(created.status_code, 201)
        id = created.json["dados"]["id"]
        self.assertEqual(self.client.get(f"/produtos/{id}").json["dados"]["nome"], attack)
        self.assertEqual(self.client.put(f"/produtos/{id}", headers=self.admin, json=product).status_code, 200)
        for field in ("q", "categoria"):
            response = self.client.get("/produtos/busca", query_string={field: "' OR 1=1 --"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["dados"], [])
        self.assertEqual(self.order(items=[{"produto_id": "1 OR 1=1", "quantidade": 1}]).status_code, 400)
        self.assertEqual(self.db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0], 2)

    def test_order_validation_and_duplicate_aggregation(self):
        for quantity in (-1, 0, True, 1.5, "1", None, 1000001):
            with self.subTest(quantity=quantity):
                self.assertEqual(self.order(quantity).status_code, 400)
        for items in ([], {}, [None], [{"produto_id": 1}], [{"produto_id": 999, "quantidade": 1}]):
            self.assertEqual(self.order(items=items).status_code, 400)
        self.assertEqual(self.order(items=[{"produto_id": 1, "quantidade": 6}] * 2).status_code, 400)
        order = self.order(items=[{"produto_id": 1, "quantidade": 2}] * 2)
        self.assertEqual(order.status_code, 201)
        self.assertEqual(order.json["dados"]["total"], 40)
        self.assertEqual(self.db().execute("SELECT estoque FROM produtos WHERE id=1").fetchone()[0], 6)
        self.assertEqual(self.db().execute("SELECT COUNT(*) FROM itens_pedido").fetchone()[0], 1)

    def test_status_transition_and_idempotent_cancellation(self):
        id = self.order().json["dados"]["pedido_id"]
        self.assertEqual(self.status(id, "entregue").status_code, 409)
        self.assertEqual(self.status(id, "aprovado").status_code, 200)
        self.assertEqual(self.status(id, "cancelado").status_code, 200)
        self.assertEqual(self.status(id, "cancelado").status_code, 200)
        self.assertEqual(self.db().execute("SELECT estoque FROM produtos WHERE id=1").fetchone()[0], 10)
        self.assertEqual(self.status(id, "pendente").status_code, 409)
        second = self.order().json["dados"]["pedido_id"]
        for status in ("aprovado", "enviado", "entregue"):
            self.assertEqual(self.status(second, status).status_code, 200)
        self.assertEqual(self.status(second, "cancelado").status_code, 409)
        self.assertEqual(self.status(second, []).status_code, 400)
        self.assertEqual(self.status(999, "aprovado").status_code, 404)

    def test_rollback_after_debit_and_safe_internal_error(self):
        with patch.object(Orders, "add_item", side_effect=RuntimeError("SQL segredo senha valor")):
            response = self.order()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json["erro"], "Erro interno")
        self.assertNotIn("segredo", response.get_data(as_text=True))
        db = self.db()
        self.assertEqual(db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0], 0)
        self.assertEqual(db.execute("SELECT estoque FROM produtos WHERE id=1").fetchone()[0], 10)
        self.assertEqual(self.order().status_code, 201)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0], 1)

    def test_cancel_rollback(self):
        id = self.order().json["dados"]["pedido_id"]
        with patch.object(Orders, "set_status", side_effect=RuntimeError("fail")):
            self.assertEqual(self.status(id, "cancelado").status_code, 500)
        db = self.db()
        self.assertEqual(db.execute("SELECT estoque FROM produtos WHERE id=1").fetchone()[0], 8)
        self.assertEqual(db.execute("SELECT status FROM pedidos WHERE id=?", (id,)).fetchone()[0], "pendente")

    def test_concurrent_orders_do_not_oversell(self):
        def place(_):
            with self.app.test_client() as client:
                return client.post("/pedidos", headers=self.user, json={"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 6}]}).status_code
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(place, range(2)))
        self.assertEqual(sorted(statuses), [201, 400])
        self.assertEqual(self.db().execute("SELECT estoque FROM produtos WHERE id=1").fetchone()[0], 4)

    def test_concurrent_cancellations_restore_once(self):
        id = self.order().json["dados"]["pedido_id"]
        def cancel(_):
            with self.app.test_client() as client:
                return client.put(f"/pedidos/{id}/status", headers=self.admin, json={"status": "cancelado"}).status_code
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(list(pool.map(cancel, range(2))), [200, 200])
        self.assertEqual(self.db().execute("SELECT estoque FROM produtos WHERE id=1").fetchone()[0], 10)

    def test_shared_validation_and_invalid_requests(self):
        for changes in ({"nome": "a"}, {"nome": None}, {"preco": "10"}, {"preco": True}, {"preco": float("nan")},
                        {"preco": float("inf")}, {"preco": 10**400}, {"estoque": 0.5}, {"estoque": -1}, {"categoria": "invalida"}):
            for method, path in (("post", "/produtos"), ("put", "/produtos/1")):
                with self.subTest(changes=changes, method=method):
                    self.assertEqual(getattr(self.client, method)(path, headers=self.admin, json={**self.product, **changes}).status_code, 400)
        for value in (None, [], "texto", 1):
            self.assertEqual(self.client.post("/usuarios", data=json.dumps(value), content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/usuarios", data="{", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/usuarios", data="{}", content_type="text/plain").status_code, 415)
        for query in ("preco_min=abc", "preco_max=nan", "preco_min=10&preco_max=1", "page=0", "per_page=101"):
            self.assertEqual(self.client.get("/produtos/busca?" + query).status_code, 400)
        self.assertEqual(self.client.get("/produtos/busca?preco_max=0").json["dados"], [])

    def test_missing_records_and_integrity(self):
        for method, path, data in (("get", "/produtos/999", None), ("put", "/produtos/999", self.product),
                                   ("delete", "/produtos/999", None), ("get", "/usuarios/999", None)):
            self.assertEqual(getattr(self.client, method)(path, headers=self.admin, json=data).status_code, 404)
        self.assertEqual(self.client.post("/pedidos", headers=self.admin, json={"usuario_id": 999, "itens": [{"produto_id": 1, "quantidade": 1}]}).status_code, 404)
        duplicate = {"nome": "Duplicado", "email": "PESSOA2@example.test", "senha": self.password}
        self.assertEqual(self.client.post("/usuarios", json=duplicate).status_code, 409)
        self.order()
        self.assertEqual(self.client.delete("/produtos/1", headers=self.admin).status_code, 409)
        db = self.db()
        for sql, args in (("INSERT INTO pedidos(usuario_id,total) VALUES (?,?)", (999, 1)),
                          ("UPDATE produtos SET estoque=? WHERE id=1", (-1,)),
                          ("UPDATE usuarios SET email=? WHERE id=3", ("pessoa2@example.test",))):
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute(sql, args)
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_order_query_count_and_pagination(self):
        for _ in range(5):
            self.assertEqual(self.order(1).status_code, 201)
        with self.app.app_context():
            statements = []
            db = get_db()
            db.set_trace_callback(statements.append)
            response = self.client.get("/pedidos?per_page=2&page=2", headers=self.admin)
            db.set_trace_callback(None)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json["dados"]], [3, 4])
        selects = [sql for sql in statements if sql.lstrip().upper().startswith("SELECT")]
        self.assertEqual(len(selects), 3)  # 1 identity lookup + 2 batched order queries.
        self.assertEqual(response.json["dados"][0]["itens"][0]["produto_nome"], "Produto de teste")
        self.assertEqual(self.client.get("/pedidos/usuario/3", headers=self.other).json["dados"], [])

    def test_connection_lifecycle_and_configuration(self):
        with self.app.app_context():
            first = get_db()
            self.assertIs(first, get_db())
        with self.assertRaises(sqlite3.ProgrammingError):
            first.execute("SELECT 1")
        with self.app.app_context():
            self.assertIsNot(first, get_db())
        self.assertFalse(self.app.debug)
        with self.assertRaises(RuntimeError):
            create_app({"SECRET_KEY": None})
        absent = Path(self.temp.name) / "absent.db"
        app = create_app({"SECRET_KEY": secrets.token_hex(32), "DATABASE": str(absent)})
        self.assertFalse(absent.exists())
        self.assertEqual(app.test_client().get("/health").status_code, 503)
        self.assertFalse(absent.exists())

    def test_report_contract(self):
        self.order()
        report = self.client.get("/relatorios/vendas", headers=self.admin).json["dados"]
        self.assertEqual(report, {"total_pedidos": 1, "faturamento_bruto": 20.0, "desconto_aplicavel": 0,
                                "faturamento_liquido": 20.0, "pedidos_pendentes": 1, "pedidos_aprovados": 0,
                                "pedidos_cancelados": 0, "ticket_medio": 20.0})

    def test_cli_initialization_and_admin(self):
        runner = self.app.test_cli_runner()
        before = self.path.read_bytes()
        self.assertNotEqual(runner.invoke(args=["init-db"]).exit_code, 0)
        self.assertEqual(before, self.path.read_bytes())
        result = runner.invoke(args=["create-admin", "--nome", "Novo Admin", "--email", "adminnovo@example.test"],
                               input=self.password + "\n" + self.password + "\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(self.db().execute("SELECT tipo FROM usuarios WHERE email='adminnovo@example.test'").fetchone()[0], "admin")


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "old.db"
        self.destination = Path(self.temp.name) / "new.db"
        db = sqlite3.connect(self.source)
        db.executescript("""
            CREATE TABLE usuarios(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT,email TEXT,senha TEXT,tipo TEXT,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE produtos(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT,descricao TEXT,preco REAL,estoque INTEGER,categoria TEXT,ativo INTEGER,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE pedidos(id INTEGER PRIMARY KEY AUTOINCREMENT,usuario_id INTEGER,status TEXT,total REAL,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE itens_pedido(id INTEGER PRIMARY KEY AUTOINCREMENT,pedido_id INTEGER,produto_id INTEGER,quantidade INTEGER,preco_unitario REAL);
            INSERT INTO usuarios(nome,email,senha,tipo) VALUES ('Pessoa','teste@example.test','legada','cliente');
            INSERT INTO produtos(nome,descricao,preco,estoque,categoria,ativo) VALUES ('Produto','',10,8,'geral',1);
            INSERT INTO pedidos(usuario_id,status,total) VALUES (1,'pendente',20);
            INSERT INTO itens_pedido(pedido_id,produto_id,quantidade,preco_unitario) VALUES (1,1,2,10);
        """)
        db.close()

    def test_migration_preserves_data_hashes_passwords_and_source(self):
        before = self.source.read_bytes()
        migrate_legacy(self.source, self.destination)
        self.assertEqual(before, self.source.read_bytes())
        db = connect(self.destination)
        self.addCleanup(db.close)
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
        self.assertTrue(check_password_hash(db.execute("SELECT senha_hash FROM usuarios").fetchone()[0], "legada"))
        self.assertEqual(db.execute("SELECT total FROM pedidos").fetchone()[0], 20)
        self.assertEqual(db.execute("SELECT estoque FROM produtos").fetchone()[0], 8)
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
        with self.assertRaises(FileExistsError):
            migrate_legacy(self.source, self.destination)

    def test_bad_legacy_data_aborts_without_loss(self):
        db = sqlite3.connect(self.source)
        db.execute("INSERT INTO usuarios(nome,email,senha,tipo) VALUES ('Duplicada','TESTE@example.test','legada','cliente')")
        db.commit()
        db.close()
        before = self.source.read_bytes()
        with self.assertRaises(sqlite3.IntegrityError):
            migrate_legacy(self.source, self.destination)
        self.assertEqual(before, self.source.read_bytes())
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
