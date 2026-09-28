"""Contract coverage over WSGI and, optionally, a real localhost HTTP server."""
import os
from threading import Thread
from types import SimpleNamespace

import pytest
import requests
from werkzeug.serving import make_server

from database import db
from models.task import Task
from sqlalchemy.exc import OperationalError


@pytest.fixture
def api(client):
    if os.getenv('TASK_API_LIVE_HTTP') != '1':
        yield client
        return
    server = make_server('127.0.0.1', 0, client.application)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    class HTTPClient:
        application = client.application

        def open(self, path, method='GET', **kwargs):
            response = requests.request(method, f'http://127.0.0.1:{server.server_port}{path}',
                                        timeout=5, **kwargs)
            return SimpleNamespace(status_code=response.status_code, get_json=response.json)

        def get(self, path, **kwargs): return self.open(path, **kwargs)
        def post(self, path, **kwargs): return self.open(path, method='POST', **kwargs)
        def put(self, path, **kwargs): return self.open(path, method='PUT', **kwargs)
        def delete(self, path, **kwargs): return self.open(path, method='DELETE', **kwargs)

    try:
        yield HTTPClient()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def call(api, method, path, status=200, **kwargs):
    response = getattr(api, method)(path, **kwargs)
    assert response.status_code == status, (method, path, response.status_code, response.get_json())
    return response.get_json()


def login(api, email='admin@test.local', password='strong-pass-1'):
    body = call(api, 'post', '/login', json={'email': email, 'password': password})
    assert 'password' not in body['user']
    return {'Authorization': 'Bearer ' + body['token']}


def test_summary_and_user_report(api):
    headers = login(api)
    empty = call(api, 'get', '/reports/summary', headers=headers)
    assert empty['overview'] == {'total_tasks': 0, 'total_users': 1, 'total_categories': 0}
    assert empty['user_productivity'][0]['completion_rate'] == 0
    category = call(api, 'post', '/categories', 201, headers=headers, json={'name': 'Work'})
    user = call(api, 'post', '/users', 201, json={
        'name': 'Worker', 'email': 'worker@test.local', 'password': 'strong-pass-2'})
    call(api, 'post', '/tasks', 201, headers=headers, json={
        'title': 'Overdue task', 'user_id': user['id'], 'category_id': category['id'],
        'priority': 1, 'due_date': '2000-01-01T00:00:00Z'})
    task = call(api, 'post', '/tasks', 201, headers=headers, json={
        'title': 'Completed task', 'user_id': user['id'], 'priority': 2})
    call(api, 'put', f"/tasks/{task['id']}", headers=headers, json={'status': 'done'})
    summary = call(api, 'get', '/reports/summary', headers=headers)
    assert summary['overview'] == {'total_tasks': 2, 'total_users': 2, 'total_categories': 1}
    assert summary['tasks_by_status'] == {'pending': 1, 'in_progress': 0, 'done': 1, 'cancelled': 0}
    assert summary['tasks_by_priority'] == {'critical': 1, 'high': 1, 'medium': 0, 'low': 0, 'minimal': 0}
    assert summary['overdue']['count'] == 1
    assert summary['overdue']['tasks'][0]['title'] == 'Overdue task'
    assert summary['recent_activity'] == {'tasks_created_last_7_days': 2, 'tasks_completed_last_7_days': 1}
    productivity = {row['user_id']: row for row in summary['user_productivity']}
    assert productivity[user['id']]['completion_rate'] == 50.0
    assert productivity[1]['total_tasks'] == 0
    report = call(api, 'get', f"/reports/user/{user['id']}", headers=headers)
    assert report['statistics'] == {'total_tasks': 2, 'done': 1, 'pending': 1,
        'in_progress': 0, 'cancelled': 0, 'overdue': 1, 'high_priority': 2, 'completion_rate': 50.0}
    call(api, 'get', '/reports/user/99999', 404, headers=headers)


def test_category_crud_and_conflicts(api):
    headers = login(api)
    call(api, 'post', '/categories', 400, headers=headers, json={'name': ''})
    call(api, 'post', '/categories', 400, headers=headers, json={'name': 'Bad', 'color': 'red'})
    category = call(api, 'post', '/categories', 201, headers=headers, json={'name': 'Work'})
    path = f"/categories/{category['id']}"
    assert category['color'] == '#000000'
    call(api, 'post', '/categories', 409, headers=headers, json={'name': 'Work'})
    rows = call(api, 'get', '/categories', headers=headers)
    assert len(rows) == 1 and rows[0]['task_count'] == 0
    call(api, 'post', '/tasks', 201, headers=headers, json={'title': 'Linked task', 'category_id': category['id']})
    assert call(api, 'get', '/categories', headers=headers)[0]['task_count'] == 1
    call(api, 'put', path, 400, headers=headers, json={'name': ''})
    assert call(api, 'get', '/categories', headers=headers)[0]['name'] == 'Work'
    assert call(api, 'put', path, headers=headers, json={'name': 'New', 'color': '#aabbcc'})['name'] == 'New'
    assert call(api, 'delete', path, headers=headers) == {'message': 'Categoria deletada'}
    assert call(api, 'get', '/categories', headers=headers) == []
    call(api, 'put', path, 404, headers=headers, json={'name': 'Missing'})
    call(api, 'delete', path, 404, headers=headers)


def test_task_crud_search_stats_and_validation(api):
    headers = login(api)
    call(api, 'post', '/tasks', 400, headers=headers, json={'title': 'x'})
    call(api, 'post', '/tasks', 404, headers=headers, json={'title': 'Missing user', 'user_id': 99999})
    task = call(api, 'post', '/tasks', 201, headers=headers,
                json={'title': 'Find needle', 'priority': 2, 'tags': ['one']})
    path = f"/tasks/{task['id']}"
    assert call(api, 'get', path, headers=headers)['tags'] == ['one']
    assert len(call(api, 'get', '/tasks', headers=headers)) == 1
    assert len(call(api, 'get', '/tasks/search?q=needle&priority=2&status=pending', headers=headers)) == 1
    assert call(api, 'get', '/tasks/search?q=absent', headers=headers) == []
    assert call(api, 'get', '/tasks/search?priority=bad', 400, headers=headers) == {'error': 'Prioridade inválida'}
    call(api, 'put', path, 400, headers=headers, json={'priority': 8})
    assert call(api, 'get', path, headers=headers)['priority'] == 2
    assert call(api, 'put', path, headers=headers, json={'status': 'done'})['status'] == 'done'
    assert call(api, 'get', '/tasks/stats', headers=headers) == {
        'total': 1, 'pending': 0, 'in_progress': 0, 'done': 1, 'cancelled': 0, 'overdue': 0}
    call(api, 'delete', path, headers=headers)
    call(api, 'get', path, 404, headers=headers)
    call(api, 'put', path, 404, headers=headers, json={'title': 'Missing'})
    call(api, 'delete', path, 404, headers=headers)


def test_user_crud_login_and_permissions(api):
    admin = login(api)
    assert call(api, 'post', '/users', 400, json={
        'name': 'Missing password', 'email': 'missing@test.local'}) == {'error': 'Senha é obrigatória'}
    user = call(api, 'post', '/users', 201, json={'name': 'Member', 'email': 'member@test.local',
        'password': 'strong-pass-2', 'role': 'admin', 'active': False})
    assert user['role'] == 'user' and user['active'] is True
    path = f"/users/{user['id']}"
    member = login(api, 'member@test.local', 'strong-pass-2')
    call(api, 'post', '/login', 401, json={'email': 'member@test.local', 'password': 'wrong'})
    call(api, 'post', '/users', 409, json={'name': 'Duplicate', 'email': 'member@test.local', 'password': 'strong-pass-2'})
    call(api, 'get', '/users', 403, headers=member)
    call(api, 'put', '/users/1', 403, headers=member, json={'name': 'Hacked'})
    call(api, 'put', path, 403, headers=member, json={'role': 'admin'})
    call(api, 'put', path, 400, headers=member, json={'email': 'bad'})
    assert call(api, 'put', path, headers=member, json={'name': 'Renamed'})['name'] == 'Renamed'
    call(api, 'post', '/tasks', 201, headers=admin, json={'title': 'Member task', 'user_id': user['id']})
    assert len(call(api, 'get', path, headers=member)['tasks']) == 1
    assert len(call(api, 'get', path + '/tasks', headers=member)) == 1
    users = call(api, 'get', '/users', headers=admin)
    assert next(row for row in users if row['id'] == user['id'])['task_count'] == 1
    call(api, 'put', path, headers=admin, json={'active': False})
    call(api, 'post', '/login', 403, json={'email': 'member@test.local', 'password': 'strong-pass-2'})
    call(api, 'delete', path, headers=admin)
    for suffix in ('', '/tasks'):
        call(api, 'get', path + suffix, 404, headers=admin)
    call(api, 'put', path, 404, headers=admin, json={'name': 'Missing'})
    call(api, 'delete', path, 404, headers=admin)


@pytest.mark.parametrize('path', ['/tasks', '/tasks/stats', '/categories', '/users', '/reports/summary', '/reports/user/1'])
def test_anonymous_access(api, path):
    call(api, 'get', path, 401)


def test_regular_user_cannot_manage_or_read_summary(api):
    call(api, 'post', '/users', 201, json={'name': 'Member', 'email': 'member@test.local', 'password': 'strong-pass-2'})
    member = login(api, 'member@test.local', 'strong-pass-2')
    call(api, 'get', '/reports/summary', 403, headers=member)
    call(api, 'post', '/categories', 403, headers=member, json={'name': 'Blocked'})
    call(api, 'post', '/tasks', 403, headers=member, json={'title': 'Blocked'})
    call(api, 'delete', '/users/1', 403, headers=member)


def test_commit_failure_rolls_back_and_hides_details(api, monkeypatch):
    headers = login(api)
    with monkeypatch.context() as patch:
        def fail_commit():
            raise OperationalError('private SQL', {}, Exception('private database detail'))
        patch.setattr(db.session, 'commit', fail_commit)
        assert call(api, 'post', '/tasks', 500, headers=headers,
                    json={'title': 'Must rollback'}) == {'error': 'Erro interno'}
    assert call(api, 'get', '/tasks', headers=headers) == []
    call(api, 'post', '/tasks', 201, headers=headers, json={'title': 'Next request works'})
    with api.application.app_context():
        assert Task.query.count() == 1


def test_readiness_and_http_errors(api):
    assert call(api, 'get', '/health') == {'status': 'ok'}
    assert call(api, 'get', '/') == {'message': 'Task Manager API', 'version': '1.0'}
    assert call(api, 'get', '/missing', 404) == {'error': 'Recurso não encontrado'}
    assert call(api, 'post', '/health', 405) == {'error': 'Método não permitido'}
