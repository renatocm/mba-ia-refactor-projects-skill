import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from app import create_app
from database import db
from models.user import User

@pytest.fixture
def client(tmp_path):
    class TestConfig:
        TESTING=True
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'test.db'}"
        SQLALCHEMY_TRACK_MODIFICATIONS=False
        SECRET_KEY='test-key'
        AUTH_TOKEN_TTL=3600
    app=create_app(TestConfig)
    with app.app_context():
        db.create_all()
        user=User(name='Admin',email='admin@test.local',role='admin'); user.set_password('strong-pass-1'); db.session.add(user); db.session.commit()
    return app.test_client()
