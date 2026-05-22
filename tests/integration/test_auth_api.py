import pytest
import json
from app import create_app, db

@pytest.fixture
def client():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        with app.test_client() as client:
            yield client
        db.drop_all()

class TestAuthAPI:
    def test_register_success(self, client):
        response = client.post('/api/auth/register',
            data=json.dumps({'username': 'newuser', 'password': 'pass123', 'email': 'new@test.com'}),
            content_type='application/json')
        assert response.status_code == 201

    def test_register_duplicate(self, client):
        payload = {'username': 'dupuser', 'password': 'pass', 'email': 'a@b.com'}
        client.post('/api/auth/register',
            data=json.dumps(payload), content_type='application/json')
        response = client.post('/api/auth/register',
            data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 409

    def test_login_success(self, client):
        client.post('/api/auth/register',
            data=json.dumps({'username': 'loginuser', 'password': 'mypass'}),
            content_type='application/json')
        response = client.post('/api/auth/login',
            data=json.dumps({'username': 'loginuser', 'password': 'mypass'}),
            content_type='application/json')
        assert response.status_code == 200
        assert 'access_token' in json.loads(response.data)

    def test_login_wrong_password(self, client):
        client.post('/api/auth/register',
            data=json.dumps({'username': 'wrongpass', 'password': 'correct'}),
            content_type='application/json')
        response = client.post('/api/auth/login',
            data=json.dumps({'username': 'wrongpass', 'password': 'wrong'}),
            content_type='application/json')
        assert response.status_code == 401

    def test_health_endpoint(self, client):
        response = client.get('/health')
        assert response.status_code == 200