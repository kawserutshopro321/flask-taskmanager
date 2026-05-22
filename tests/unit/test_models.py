import pytest
from app import create_app, db
from app.models import User, Task

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

class TestUserModel:
    def test_password_hashing(self, app):
        with app.app_context():
            user = User(username='testuser', email='test@test.com')
            user.set_password('securepassword')
            assert user.check_password('securepassword') is True

    def test_wrong_password_fails(self, app):
        with app.app_context():
            user = User(username='testuser2', email='test2@test.com')
            user.set_password('correct')
            assert user.check_password('wrong') is False

    def test_user_to_dict_no_password(self, app):
        with app.app_context():
            user = User(username='dictuser', email='dict@test.com')
            result = user.to_dict()
            assert 'username' in result
            assert 'password_hash' not in result

class TestTaskModel:
    def test_task_defaults(self, app):
        with app.app_context():
            db.create_all()
            user = User(username='owner', email='owner@test.com')
            user.set_password('pass')
            db.session.add(user)
            db.session.commit()
            task = Task(title='Test Task', user_id=user.id)
            db.session.add(task)
            db.session.commit()
            assert task.completed is False
            assert task.priority == 'medium'

    def test_task_to_dict(self, app):
        with app.app_context():
            db.create_all()
            user = User(username='owner2', email='owner2@test.com')
            user.set_password('pass')
            db.session.add(user)
            db.session.commit()
            task = Task(title='My Task', user_id=user.id, priority='high')
            db.session.add(task)
            db.session.commit()
            d = task.to_dict()
            assert d['title'] == 'My Task'
            assert d['priority'] == 'high'