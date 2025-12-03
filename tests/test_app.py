import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def restore_activities():
    # Make a deep copy of the in-memory activities and restore after each test
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    return TestClient(app)


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect some known activity from the seeded data
    assert "Chess Club" in data


def test_signup_success(client):
    email = "tester1@mergington.edu"
    resp = client.post("/activities/Chess%20Club/signup?email=" + email)
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body["message"]
    # Changes are applied to the in-memory activities
    assert email in activities["Chess Club"]["participants"]


def test_signup_already_signed(client):
    # michael@... is already in seeded participants
    resp = client.post("/activities/Chess%20Club/signup?email=michael@mergington.edu")
    assert resp.status_code == 400


def test_unregister_success(client):
    # first sign up a temporary user, then unregister
    email = "tempremove@mergington.edu"
    r = client.post("/activities/Programming%20Class/signup?email=" + email)
    assert r.status_code == 200

    d = client.delete("/activities/Programming%20Class/participants?email=" + email)
    assert d.status_code == 200
    body = d.json()
    assert "Unregistered" in body["message"]
    assert email not in activities["Programming Class"]["participants"]


def test_unregister_not_found(client):
    # Try to remove a user that doesn't exist
    r = client.delete("/activities/Gym%20Class/participants?email=nosuch@mergington.edu")
    assert r.status_code == 404


def test_activity_not_found(client):
    r = client.get("/activities/Nonexistent")
    # GET /activities returns the full dict; but requesting a specific activity is not available.
    # Check that posting to a non-existing activity returns 404
    p = client.post("/activities/NoActivity/signup?email=a@b.com")
    assert p.status_code == 404
