"""Tests for Paddle webhook API."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_paddle_webhook_no_signature():
    """Test Paddle webhook without signature."""
    response = client.post(
        "/api/paddle/webhook",
        json={"event_type": "subscription.created"},
    )
    assert response.status_code == 422  # Missing header


def test_paddle_webhook_invalid_signature():
    """Test Paddle webhook with invalid signature."""
    payload = {"event_type": "subscription.created", "data": {"id": "123"}}
    response = client.post(
        "/api/paddle/webhook",
        json=payload,
        headers={"Paddle-Signature": "invalid-signature"},
    )
    # Should fail signature verification
    assert response.status_code in [401, 422]










