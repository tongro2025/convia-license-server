"""Tests for admin reset functionality."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.license import License
from app.models.license_usage import LicenseUsage
from app.models.machine_binding import MachineBinding


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_api_key():
    """Admin API key for testing."""
    # 실제 환경에서는 설정에서 가져와야 함
    return "test-admin-api-key"


@pytest.fixture
def test_license(db: Session):
    """Create a test license."""
    license_obj = License(
        paddle_subscription_id="test-subscription-123",
        email="test@example.com",
        allowed_containers=5,
        status="active",
    )
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    return license_obj


@pytest.fixture
def test_usage(db: Session, test_license: License):
    """Create test container usage."""
    usage1 = LicenseUsage(
        license_id=test_license.id,
        machine_id="machine-1",
        container_id="container-1",
    )
    usage2 = LicenseUsage(
        license_id=test_license.id,
        machine_id="machine-1",
        container_id="container-2",
    )
    db.add(usage1)
    db.add(usage2)
    db.commit()
    return [usage1, usage2]


@pytest.fixture
def test_machine_bindings(db: Session, test_license: License):
    """Create test machine bindings."""
    binding1 = MachineBinding(
        license_id=test_license.id,
        machine_id="machine-1",
    )
    binding2 = MachineBinding(
        license_id=test_license.id,
        machine_id="machine-2",
    )
    db.add(binding1)
    db.add(binding2)
    db.commit()
    return [binding1, binding2]


def test_reset_containers(client: TestClient, db: Session, test_license: License, test_usage, admin_api_key: str):
    """Test resetting container usage."""
    # Verify containers exist before reset
    usage_count_before = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == test_license.id
    ).count()
    assert usage_count_before == 2

    # Reset containers
    response = client.post(
        f"/api/admin/licenses/{test_license.id}/reset-containers",
        headers={"X-Admin-API-Key": admin_api_key},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Container usage reset"

    # Verify containers are deleted
    usage_count_after = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == test_license.id
    ).count()
    assert usage_count_after == 0


def test_reset_machines(client: TestClient, db: Session, test_license: License, test_machine_bindings, admin_api_key: str):
    """Test resetting machine bindings."""
    # Verify bindings exist before reset
    binding_count_before = db.query(MachineBinding).filter(
        MachineBinding.license_id == test_license.id
    ).count()
    assert binding_count_before == 2

    # Reset machines
    response = client.post(
        f"/api/admin/licenses/{test_license.id}/reset-machines",
        headers={"X-Admin-API-Key": admin_api_key},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Machine bindings reset"

    # Verify bindings are deleted
    binding_count_after = db.query(MachineBinding).filter(
        MachineBinding.license_id == test_license.id
    ).count()
    assert binding_count_after == 0


def test_reset_containers_and_verify_usage(client: TestClient, db: Session, test_license: License, test_usage, admin_api_key: str):
    """Test that resetting containers actually clears usage and allows new containers."""
    # Initial state: 2 containers in use
    usage_count_before = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == test_license.id
    ).count()
    assert usage_count_before == 2

    # Reset containers
    response = client.post(
        f"/api/admin/licenses/{test_license.id}/reset-containers",
        headers={"X-Admin-API-Key": admin_api_key},
    )
    assert response.status_code == 200

    # Verify usage is cleared
    usage_count_after = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == test_license.id
    ).count()
    assert usage_count_after == 0

    # Verify we can add new containers after reset
    # This simulates what happens when verify is called after reset
    new_usage = LicenseUsage(
        license_id=test_license.id,
        machine_id="machine-3",
        container_id="container-3",
    )
    db.add(new_usage)
    db.commit()

    # Verify new usage was added
    usage_count_final = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == test_license.id
    ).count()
    assert usage_count_final == 1


def test_reset_machines_and_verify_binding(client: TestClient, db: Session, test_license: License, test_machine_bindings, admin_api_key: str):
    """Test that resetting machines actually clears bindings and allows new bindings."""
    # Initial state: 2 machines bound
    binding_count_before = db.query(MachineBinding).filter(
        MachineBinding.license_id == test_license.id
    ).count()
    assert binding_count_before == 2

    # Reset machines
    response = client.post(
        f"/api/admin/licenses/{test_license.id}/reset-machines",
        headers={"X-Admin-API-Key": admin_api_key},
    )
    assert response.status_code == 200

    # Verify bindings are cleared
    binding_count_after = db.query(MachineBinding).filter(
        MachineBinding.license_id == test_license.id
    ).count()
    assert binding_count_after == 0

    # Verify we can add new bindings after reset
    new_binding = MachineBinding(
        license_id=test_license.id,
        machine_id="machine-3",
    )
    db.add(new_binding)
    db.commit()

    # Verify new binding was added
    binding_count_final = db.query(MachineBinding).filter(
        MachineBinding.license_id == test_license.id
    ).count()
    assert binding_count_final == 1


def test_reset_nonexistent_license(client: TestClient, admin_api_key: str):
    """Test resetting a non-existent license."""
    response = client.post(
        "/api/admin/licenses/99999/reset-containers",
        headers={"X-Admin-API-Key": admin_api_key},
    )

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_reset_without_admin_key(client: TestClient, test_license: License):
    """Test that reset requires admin API key."""
    response = client.post(
        f"/api/admin/licenses/{test_license.id}/reset-containers",
    )

    assert response.status_code == 422  # Missing header


def test_get_usage_after_reset(client: TestClient, db: Session, test_license: License, test_usage, admin_api_key: str):
    """Test getting usage information after reset."""
    # Reset containers
    client.post(
        f"/api/admin/licenses/{test_license.id}/reset-containers",
        headers={"X-Admin-API-Key": admin_api_key},
    )

    # Get usage info
    response = client.get(
        f"/api/admin/licenses/{test_license.id}/usage",
        headers={"X-Admin-API-Key": admin_api_key},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["current_usage"] == 0
    assert len(data["usage_details"]) == 0




