"""WSGI entry point; schema and administrator creation are explicit CLI commands."""
from loja import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=False)
