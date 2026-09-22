"""Start the documented entry point, exercise real HTTP, verify data, stop it.

Run from the project root: .venv/bin/python tests/smoke_http.py
Only a TemporaryDirectory database is used. Secrets/tokens are never printed.
"""
import json
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="loja-http-") as directory:
        database = str(Path(directory) / "smoke.db")
        env = {**os.environ, "SECRET_KEY": secrets.token_hex(32), "DATABASE_PATH": database,
               "HOST": "127.0.0.1", "PYTHONUNBUFFERED": "1"}
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            env["PORT"] = str(listener.getsockname()[1])
        subprocess.run([sys.executable, "-m", "flask", "--app", "app", "init-db"], cwd=ROOT, env=env,
                       check=True, capture_output=True, text=True)
        password = secrets.token_urlsafe(24)
        subprocess.run([sys.executable, "-m", "flask", "--app", "app", "create-admin", "--nome", "Smoke Admin", "--email", "admin@example.test"],
                       cwd=ROOT, env=env, input=password + "\n" + password + "\n", check=True, capture_output=True, text=True)
        base = "http://127.0.0.1:" + env["PORT"]

        def request(method, path, expected, data=None, token=None, record=True):
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = "Bearer " + token
            req = Request(base + path, data=json.dumps(data).encode() if data is not None else None,
                          method=method, headers=headers)
            try:
                response = urlopen(req, timeout=5)
            except HTTPError as error:
                response = error
            with response:
                status, payload = response.status, json.load(response)
            if record:
                results.append({"method": method, "path": path, "status": status, "expected": expected})
            assert status == expected, (method, path, status, expected)
            return payload

        with (Path(directory) / "server.log").open("w+") as log:
            process = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env, stdout=log, stderr=log)
            try:
                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError("Servidor encerrou antes da prontidão")
                    try:
                        request("GET", "/health", 200, record=False)
                        break
                    except (URLError, ConnectionError):
                        time.sleep(0.05)
                else:
                    raise RuntimeError("Servidor não ficou pronto")
                request("GET", "/", 200)
                request("GET", "/health", 200)
                request("GET", "/usuarios", 401)
                admin = request("POST", "/login", 200, {"email": "admin@example.test", "senha": password})["token"]
                user_id = request("POST", "/usuarios", 201, {"nome": "Smoke User", "email": "user@example.test", "senha": password})["dados"]["id"]
                user = request("POST", "/login", 200, {"email": "user@example.test", "senha": password})["token"]
                request("POST", "/login", 401, {"email": "user@example.test", "senha": "incorreta"})
                request("GET", "/usuarios", 200, token=admin)
                request("GET", f"/usuarios/{user_id}", 200, token=user)
                request("GET", "/usuarios/1", 403, token=user)
                request("GET", "/usuarios/999", 404, token=admin)
                product = {"nome": "Produto HTTP", "preco": 10, "estoque": 10}
                product_id = request("POST", "/produtos", 201, product, admin)["dados"]["id"]
                request("GET", "/produtos", 200)
                request("GET", "/produtos/busca?q=HTTP", 200)
                request("GET", f"/produtos/{product_id}", 200)
                request("PUT", f"/produtos/{product_id}", 200, product, admin)
                request("POST", "/produtos", 403, product, user)
                request("PUT", f"/produtos/{product_id}", 400, {**product, "preco": -1}, admin)
                request("GET", "/produtos/999", 404)
                order = {"usuario_id": user_id, "itens": [{"produto_id": product_id, "quantidade": 2}]}
                order_id = request("POST", "/pedidos", 201, order, user)["dados"]["pedido_id"]
                request("GET", "/pedidos", 200, token=admin)
                request("GET", f"/pedidos/usuario/{user_id}", 200, token=user)
                request("GET", "/pedidos/usuario/1", 403, token=user)
                request("PUT", f"/pedidos/{order_id}/status", 200, {"status": "cancelado"}, admin)
                request("PUT", f"/pedidos/{order_id}/status", 200, {"status": "cancelado"}, admin)
                request("PUT", f"/pedidos/{order_id}/status", 409, {"status": "aprovado"}, admin)
                request("PUT", "/pedidos/999/status", 404, {"status": "aprovado"}, admin)
                request("GET", "/relatorios/vendas", 200, token=admin)
                request("DELETE", f"/produtos/{product_id}", 409, token=admin)
                unused_id = request("POST", "/produtos", 201, product, admin)["dados"]["id"]
                request("DELETE", f"/produtos/{unused_id}", 200, token=admin)
                request("DELETE", f"/produtos/{unused_id}", 404, token=admin)
                for path in ("/admin/query", "/admin/reset-db"):
                    request("POST", path, 404, {"sql": "DELETE FROM produtos"}, admin)
                with sqlite3.connect(database) as db:
                    assert db.execute("SELECT estoque FROM produtos WHERE id=?", (product_id,)).fetchone()[0] == 10
                    assert db.execute("SELECT status FROM pedidos WHERE id=?", (order_id,)).fetchone()[0] == "cancelado"
                    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            log.seek(0)
            assert "Debug mode: off" in log.read()
    print(json.dumps({"boot": "ok", "debug": False, "server_stopped": True, "temporary_database_removed": True,
                      "requests": results}, indent=2))


if __name__ == "__main__":
    main()
