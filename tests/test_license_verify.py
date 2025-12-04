"""Tests for license verification API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_verify_license_not_found():
    """Test license verification with non-existent license."""
    response = client.post(
        "/api/license/verify",
        json={
            "license_key": "invalid-key",
            "machine_id": "machine-123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"








