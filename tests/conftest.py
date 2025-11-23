"""
Pytest configuration and shared fixtures for testing
"""
import pytest
import os
import tempfile
from datetime import datetime, timezone
from app import app as flask_app
from models import db, User, Todo, Category, PriorityLevel


@pytest.fixture(scope='function')
def app():
    """Create and configure a test Flask application instance"""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SECRET_KEY': 'test-secret-key'
    })
    
    # Create the database and tables
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()
    
    # Clean up the temporary database file
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def app_context(app):
    """Provide an application context for tests"""
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def test_db(app_context):
    """Provide a clean database for each test"""
    yield db
    db.session.rollback()


@pytest.fixture(scope='function')
def test_client(app):
    """Provide a test client for making requests"""
    return app.test_client()


@pytest.fixture(scope='function')
def test_user(app_context, test_db):
    """Create a test user"""
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('testpassword123')
    test_db.session.add(user)
    test_db.session.commit()
    return user


@pytest.fixture(scope='function')
def authenticated_client(test_client, test_user):
    """Provide an authenticated test client"""
    test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    }, follow_redirects=True)
    return test_client


@pytest.fixture(scope='function')
def test_category(app_context, test_db, test_user):
    """Create a test category"""
    category = Category(
        name='Work',
        color='#ff0000',
        user_id=test_user.id
    )
    test_db.session.add(category)
    test_db.session.commit()
    return category


@pytest.fixture(scope='function')
def test_todo(app_context, test_db, test_user):
    """Create a test todo"""
    todo = Todo(
        title='Test Todo',
        description='Test Description',
        user_id=test_user.id,
        priority=PriorityLevel.MEDIUM
    )
    test_db.session.add(todo)
    test_db.session.commit()
    return todo
