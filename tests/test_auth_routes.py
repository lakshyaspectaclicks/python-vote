from app.utils.exceptions import AuthenticationError


def test_admin_login_success(monkeypatch, client):
    from app.routes import auth as auth_routes

    def fake_login(**kwargs):
        assert kwargs["username"] == "admin"
        return {"id": 1, "username": "admin", "full_name": "Admin User"}

    monkeypatch.setattr(auth_routes.auth_service, "login", fake_login)
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "Admin@1234"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/")


def test_admin_login_failure(monkeypatch, client):
    from app.routes import auth as auth_routes

    def fake_login(**kwargs):
        raise AuthenticationError("Invalid credentials.")

    monkeypatch.setattr(auth_routes.auth_service, "login", fake_login)
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid credentials." in response.data


def test_protected_admin_route_redirects_when_not_logged_in(client):
    response = client.get("/admin/", follow_redirects=False)
    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]

