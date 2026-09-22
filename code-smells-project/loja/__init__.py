from flask import Flask
from flask_cors import CORS

from loja.config import environment, validate
from loja.database import close_db
from loja.errors import register_errors
from loja.services.users import TokenAuth


def create_app(config=None):
    app = Flask(__name__, static_folder=None)
    app.config.from_mapping(environment())
    if config:
        app.config.update(config)
    validate(app.config)
    app.extensions["token_auth"] = TokenAuth(app.config["SECRET_KEY"], app.config["TOKEN_TTL"])
    app.teardown_appcontext(close_db)
    register_errors(app)
    from loja.cli import register_cli
    from loja.routes import blueprint
    register_cli(app)
    app.register_blueprint(blueprint())
    if app.config["CORS_ORIGINS"]:
        CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=False)
    return app
