# tasks.py
import time
import pytest

def say_hello(name):
    print(f"Hello, {name}!")
    time.sleep(2)
    return f"Greeted {name}"

def test_say_hello():
    """Run the helper to ensure it behaves as expected."""
    result = say_hello("pytest")
    assert result == "Greeted pytest"

# Test mongo connection
from app_v2.adapters.mongo.client import db

def test_mongo_connection():
    """Verify we can obtain the database object from the mongo client.

    This test should not execute during module import. It will be collected and
    executed by pytest. If a connection cannot be obtained the test will fail
    with a helpful message.
    """
    try:
        client = db()
        # Basic sanity assertion: db() should return a database-like object
        assert client is not None
    except Exception as e:
        pytest.fail(f"MongoDB connection failed: {e}")
        
# Test user login
from app_v2.api.v1.routers.auth import auth_router
from fastapi.testclient import TestClient

client = TestClient(auth_router)
def test_user_login():
    """Test the user login endpoint."""
    response = client.post(
        "/api/v1/login",
        json={"email": "test@example.com", "password": "password123"}
    )