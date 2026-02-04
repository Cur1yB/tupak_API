# test_main.py
import pytest
from fastapi.testclient import TestClient
from .. import database
import app


@pytest.fixture()
def client():
    """
    Fresh TestClient per test.
    """
    return TestClient(app.app)


@pytest.fixture(autouse=True)
def reset_inmemory_db(): 
    """
    Reset in-memory storage before each test so tests are independent.
    """
    database.users.clear()
    database.next_id = 1
    yield
    database.users.clear()
    database.next_id = 1


@pytest.fixture()
def create_user(client):
    def _create(name: str, email: str):
        r = client.post("/users", json={"name": name, "email": email})
        assert r.status_code == 201, r.text
        return r.json()
    return _create


@pytest.mark.parametrize(
    "method,url,body,expected_status",
    [
        ("get", "/users/999", None, 404),
        ("put", "/users/999", {"name": "X"}, 404),
        ("delete", "/users/999", None, 404),
    ],
)
def test_not_found_parametrized(client, method, url, body, expected_status):
    request = getattr(client, method)
    r = request(url, json=body) if body is not None else request(url)
    assert r.status_code == expected_status


def test_crud_flow_subtests(client):
    # --- CREATE ---
    r = client.post("/users", json={"name": "Ivan", "email": "ivan@example.com"})
    assert r.status_code == 201
    user = r.json()
    assert user["id"] == 1
    assert user["name"] == "Ivan"
    assert user["email"] == "ivan@example.com"

    # --- LIST ---
    r = client.get("/users")
    assert r.status_code == 200
    users = r.json()
    assert len(users) == 1
    assert users[0]["id"] == 1

    # --- GET ONE ---
    r = client.get("/users/1")
    assert r.status_code == 200
    assert r.json()["email"] == "ivan@example.com"

    # --- UPDATE ---
    r = client.put("/users/1", json={"name": "Ivan Petrov"})
    assert r.status_code == 200
    assert r.json()["name"] == "Ivan Petrov"
    assert r.json()["email"] == "ivan@example.com"

    # --- DELETE ---
    r = client.delete("/users/1")
    assert r.status_code == 204
    assert r.text == ""

    # --- GET DELETED ---
    r = client.get("/users/1")
    assert r.status_code == 404


@pytest.mark.parametrize(
    "existing, new_user, expected_status, expected_detail",
    [
        (
            [{"name": "A", "email": "a@example.com"}],
            {"name": "B", "email": "a@example.com"},
            400,
            "Email already exists",
        ),
    ],
)
def test_create_unique_email_parametrized(client, existing, new_user, expected_status, expected_detail):
    # arrange
    for u in existing:
        r = client.post("/users", json=u)
        assert r.status_code == 201

    # act
    r = client.post("/users", json=new_user)

    # assert
    assert r.status_code == expected_status
    assert r.json()["detail"] == expected_detail


def test_update_to_existing_email_subtests(client, create_user):
    u1 = create_user("U1", "u1@example.com")
    u2 = create_user("U2", "u2@example.com")

    r = client.put(f"/users/{u2['id']}", json={"email": u1["email"]})
    assert r.status_code == 400
    assert r.json()["detail"] == "Email already exists"


@pytest.mark.parametrize(
    "payload, expected_status",
    [
        ({"name": "NoEmail"}, 422),
        ({"email": "no-name@example.com"}, 422),
        ({"name": "BadEmail", "email": "not-an-email"}, 422),
    ],
)
def test_validation_parametrized(client, payload, expected_status):
    r = client.post("/users", json=payload)
    assert r.status_code == expected_status
