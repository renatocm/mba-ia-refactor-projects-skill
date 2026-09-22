import sqlite3

import click
from flask import current_app

from loja.bootstrap import initialize, migrate_legacy
from loja.database import get_db
from loja.errors import DomainError
from loja.services.users import UserService


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Create an empty database; refuse to overwrite any existing file."""
        try:
            initialize(current_app.config["DATABASE"])
        except FileExistsError:
            raise click.ClickException("Banco já existe; init-db nunca sobrescreve arquivos.") from None
        click.echo("Banco inicializado, sem seed ou credenciais padrão.")

    @app.cli.command("create-admin")
    @click.option("--nome", prompt=True)
    @click.option("--email", prompt=True)
    @click.password_option(confirmation_prompt=True)
    def create_admin(nome, email, password):
        """Create an administrator through trusted local access only."""
        try:
            UserService(get_db()).create({"nome": nome, "email": email, "senha": password}, role="admin")
        except DomainError as error:
            raise click.ClickException(error.message) from None
        click.echo("Administrador criado.")

    @app.cli.command("migrate-legacy")
    @click.option("--source", required=True, type=click.Path(exists=True, dir_okay=False))
    @click.option("--destination", required=True, type=click.Path(dir_okay=False))
    def migrate(source, destination):
        """Copy legacy data to a new database with constraints and password hashing."""
        try:
            migrate_legacy(source, destination)
        except (sqlite3.Error, ValueError, OSError, TypeError, AttributeError):
            raise click.ClickException("Migração recusada. Verifique origem, destino novo e integridade dos dados; origem preservada.") from None
        click.echo("Migração concluída. Origem preservada; configure DATABASE_PATH para o destino após revisão.")
