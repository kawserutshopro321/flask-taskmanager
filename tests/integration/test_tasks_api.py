import pytest
import json
from app import create_app, db

@pytest.fixture
def client():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        with app.test_client() as c:
            yield c
        db.drop_all()

@pytest.fixture
def auth_headers(client):
    client.post('/api/auth/register',
        data=json.dumps({'username': 'taskuser', 'password': 'pass123'}),
        content_type='application/json')
    resp = client.post('/api/auth/login',
        data=json.dumps({'username': 'taskuser', 'password': 'pass123'}),
        content_type='application/json')
    token = json.loads(resp.data)['access_token']
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

class TestTasksAPI:
    def test_get_tasks_empty(self, client, auth_headers):
        response = client.get('/api/tasks/', headers=auth_headers)
        assert response.status_code == 200
        assert json.loads(response.data) == []

    def test_create_task(self, client, auth_headers):
        response = client.post('/api/tasks/',
            data=json.dumps({'title': 'Buy milk', 'priority': 'high'}),
            headers=auth_headers)
        assert response.status_code == 201
        assert json.loads(response.data)['title'] == 'Buy milk'

    def test_create_task_no_title(self, client, auth_headers):
        response = client.post('/api/tasks/',
            data=json.dumps({'description': 'no title'}),
            headers=auth_headers)
        assert response.status_code == 400

    def test_update_task(self, client, auth_headers):
        create = client.post('/api/tasks/',
            data=json.dumps({'title': 'Original'}), headers=auth_headers)
        task_id = json.loads(create.data)['id']
        response = client.put(f'/api/tasks/{task_id}',
            data=json.dumps({'completed': True}),
            headers=auth_headers)
        assert response.status_code == 200
        assert json.loads(response.data)['completed'] is True

    def test_delete_task(self, client, auth_headers):
        create = client.post('/api/tasks/',
            data=json.dumps({'title': 'Delete me'}), headers=auth_headers)
        task_id = json.loads(create.data)['id']
        response = client.delete(f'/api/tasks/{task_id}', headers=auth_headers)
        assert response.status_code == 200

    def test_requires_auth(self, client):
        response = client.get('/api/tasks/')
        assert response.status_code == 401