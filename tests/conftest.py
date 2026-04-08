import pytest

from app import create_app


@pytest.fixture
def app():
    app = create_app("testing")
    app.config.update(SECRET_KEY="test-secret")
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    with client.session_transaction() as sess:
        sess["admin_id"] = 1
        sess["admin_username"] = "admin"
    return client

