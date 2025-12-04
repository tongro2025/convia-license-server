"""Admin license API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.core.security import verify_admin_api_key
from app.db.session import get_db
from app.models.license import License
from app.models.license_usage import LicenseUsage
from app.models.machine_binding import MachineBinding
from app.schemas.license import LicenseOut

router = APIRouter()


@router.get("", response_model=List[LicenseOut])
async def list_licenses(
    db: Session = Depends(get_db),
    x_admin_api_key: str = Header(..., alias="X-Admin-API-Key"),
):
    """List all licenses (admin only).

    Args:
        db: Database session
        x_admin_api_key: Admin API key

    Returns:
        List of licenses
    """
    verify_admin_api_key(x_admin_api_key)

    licenses = db.query(License).all()
    return licenses


@router.get("/{license_id}", response_model=LicenseOut)
async def get_license(
    license_id: int,
    db: Session = Depends(get_db),
    x_admin_api_key: str = Header(..., alias="X-Admin-API-Key"),
):
    """Get specific license (admin only).

    Args:
        license_id: License ID
        db: Database session
        x_admin_api_key: Admin API key

    Returns:
        License details
    """
    verify_admin_api_key(x_admin_api_key)

    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )

    return license_obj


@router.post("/{license_id}/reset-machines")
async def reset_machines(
    license_id: int,
    db: Session = Depends(get_db),
    x_admin_api_key: str = Header(..., alias="X-Admin-API-Key"),
):
    """Reset machine bindings for a license (admin only).

    Args:
        license_id: License ID
        db: Database session
        x_admin_api_key: Admin API key

    Returns:
        Success message
    """
    verify_admin_api_key(x_admin_api_key)

    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )

    # Delete all machine bindings for this license
    db.query(MachineBinding).filter(
        MachineBinding.license_id == license_id
    ).delete()

    db.commit()

    return {"status": "success", "message": "Machine bindings reset"}


@router.get("/{license_id}/usage")
async def get_license_usage(
    license_id: int,
    db: Session = Depends(get_db),
    x_admin_api_key: str = Header(..., alias="X-Admin-API-Key"),
):
    """Get container usage for a license (admin only).

    Args:
        license_id: License ID
        db: Database session
        x_admin_api_key: Admin API key

    Returns:
        License usage information including container count
    """
    verify_admin_api_key(x_admin_api_key)

    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )

    # Get container usage count
    current_usage = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == license_id
    ).count()

    # Get machine bindings count
    machine_bindings_count = db.query(MachineBinding).filter(
        MachineBinding.license_id == license_id
    ).count()

    # Get detailed usage list
    usage_list = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == license_id
    ).all()

    return {
        "license_id": license_obj.id,
        "license_key": license_obj.paddle_subscription_id,
        "email": license_obj.email,
        "status": license_obj.status,
        "allowed_containers": license_obj.allowed_containers,
        "current_usage": current_usage,
        "machine_bindings_count": machine_bindings_count,
        "usage_details": [
            {
                "id": usage.id,
                "machine_id": usage.machine_id,
                "container_id": usage.container_id,
                "created_at": usage.created_at.isoformat(),
            }
            for usage in usage_list
        ],
    }


@router.post("/{license_id}/reset-containers")
async def reset_containers(
    license_id: int,
    db: Session = Depends(get_db),
    x_admin_api_key: str = Header(..., alias="X-Admin-API-Key"),
):
    """Reset container usage for a license (admin only).

    Args:
        license_id: License ID
        db: Database session
        x_admin_api_key: Admin API key

    Returns:
        Success message
    """
    verify_admin_api_key(x_admin_api_key)

    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )

    # Delete all container usage records for this license
    db.query(LicenseUsage).filter(
        LicenseUsage.license_id == license_id
    ).delete()

    db.commit()

    return {"status": "success", "message": "Container usage reset"}








