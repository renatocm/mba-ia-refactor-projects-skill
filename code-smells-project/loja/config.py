import os
from pathlib import Path


def environment():
    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY"),
        "DATABASE": os.environ.get("DATABASE_PATH", str(Path(__file__).resolve().parent.parent / "loja.db")),
        "TOKEN_TTL": int(os.environ.get("TOKEN_TTL", "3600")),
        "HOST": os.environ.get("HOST", "127.0.0.1"),
        "PORT": int(os.environ.get("PORT", "5000")),
        "DEBUG": False,
        "MAX_CONTENT_LENGTH": 1024 * 1024,
        "CORS_ORIGINS": [v.strip() for v in os.environ.get("CORS_ORIGINS", "").split(",") if v.strip()],
    }


def validate(config):
    secret = config.get("SECRET_KEY")
    if not isinstance(secret, str) or len(secret.strip()) < 32:
        raise RuntimeError("Configure SECRET_KEY com pelo menos 32 caracteres aleatórios.")
    if type(config["TOKEN_TTL"]) is not int or not 1 <= config["TOKEN_TTL"] <= 86400:
        raise RuntimeError("TOKEN_TTL deve estar entre 1 e 86400 segundos.")
    if "*" in config["CORS_ORIGINS"]:
        raise RuntimeError("CORS_ORIGINS deve listar origens explícitas.")
