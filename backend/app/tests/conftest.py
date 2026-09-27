import pytest
from mongomock_motor import AsyncMongoMockClient
import unittest.mock

# Patch motor client before any application modules are imported
mock_client = AsyncMongoMockClient()
unittest.mock.patch("motor.motor_asyncio.AsyncIOMotorClient", return_value=mock_client).start()

from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
