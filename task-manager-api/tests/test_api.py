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

def login(client):
    response=client.post('/login',json={'email':'admin@test.local','password':'strong-pass-1'})
    assert response.status_code == 200
    return {'Authorization':'Bearer '+response.get_json()['token']}

def test_auth_and_password_not_exposed(client):
    assert client.get('/tasks').status_code == 401
    headers=login(client)
    response=client.get('/users',headers=headers)
    assert response.status_code == 200
    assert 'password' not in response.get_json()[0]

def test_task_lifecycle(client):
    headers=login(client)
    created=client.post('/tasks',headers=headers,json={'title':'Test task','priority':2,'tags':['one']})
    assert created.status_code == 201
    task_id=created.get_json()['id']
    assert client.get(f'/tasks/{task_id}',headers=headers).status_code == 200
    assert client.put(f'/tasks/{task_id}',headers=headers,json={'status':'done'}).status_code == 200
    assert client.delete(f'/tasks/{task_id}',headers=headers).status_code == 200
