"""Authentication and license management routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.license import License
from app.models.license_usage import LicenseUsage
from app.models.machine_binding import MachineBinding
from app.models.magic_token import MagicToken

router = APIRouter()


@router.get("/magic-link/verify")
async def verify_magic_link(
    token: str = Query(..., description="Magic token from email link"),
    db: Session = Depends(get_db),
):
    """Verify magic link token and return license information.

    Args:
        token: Magic token from email link
        db: Database session

    Returns:
        License information if token is valid
    """
    # Find valid magic token
    magic_token = db.query(MagicToken).filter(
        MagicToken.token == token,
        MagicToken.used_at.is_(None),  # Not yet used
        MagicToken.expires_at > datetime.utcnow(),  # Not expired
    ).first()

    if not magic_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired token",
        )

    # Get license information
    license_obj = db.query(License).filter(
        License.id == magic_token.license_id
    ).first()

    if not license_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )

    # Get usage statistics
    current_usage = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == license_obj.id
    ).count()

    machine_bindings_count = db.query(MachineBinding).filter(
        MachineBinding.license_id == license_obj.id
    ).count()

    # Get usage details
    usage_list = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == license_obj.id
    ).order_by(LicenseUsage.created_at.desc()).limit(10).all()

    # Get machine bindings
    machine_bindings = db.query(MachineBinding).filter(
        MachineBinding.license_id == license_obj.id
    ).order_by(MachineBinding.created_at.desc()).limit(10).all()

    return {
        "valid": True,
        "token": token,
        "license": {
            "id": license_obj.id,
            "license_key": license_obj.paddle_subscription_id,
            "email": license_obj.email,
            "status": license_obj.status,
            "allowed_containers": license_obj.allowed_containers,
            "current_usage": current_usage,
            "machine_bindings_count": machine_bindings_count,
            "created_at": license_obj.created_at.isoformat(),
            "updated_at": license_obj.updated_at.isoformat(),
        },
        "usage": [
            {
                "id": usage.id,
                "machine_id": usage.machine_id,
                "container_id": usage.container_id,
                "created_at": usage.created_at.isoformat(),
            }
            for usage in usage_list
        ],
        "machine_bindings": [
            {
                "id": binding.id,
                "machine_id": binding.machine_id,
                "created_at": binding.created_at.isoformat(),
            }
            for binding in machine_bindings
        ],
    }


@router.get("/licenses/me")
async def get_my_license(
    token: str = Query(..., description="Magic token for authentication"),
    db: Session = Depends(get_db),
):
    """Get current user's license information using magic token.

    Args:
        token: Magic token from magic link
        db: Database session

    Returns:
        License information and usage statistics
    """
    # Find valid magic token
    magic_token = db.query(MagicToken).filter(
        MagicToken.token == token,
        MagicToken.expires_at > datetime.utcnow(),  # Not expired (used tokens are OK)
    ).first()

    if not magic_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Get license information
    license_obj = db.query(License).filter(
        License.id == magic_token.license_id
    ).first()

    if not license_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )

    # Get usage statistics
    current_usage = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == license_obj.id
    ).count()

    machine_bindings_count = db.query(MachineBinding).filter(
        MachineBinding.license_id == license_obj.id
    ).count()

    # Get all usage details
    usage_list = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == license_obj.id
    ).order_by(LicenseUsage.created_at.desc()).all()

    # Get all machine bindings
    machine_bindings = db.query(MachineBinding).filter(
        MachineBinding.license_id == license_obj.id
    ).order_by(MachineBinding.created_at.desc()).all()

    return {
        "license": {
            "id": license_obj.id,
            "license_key": license_obj.paddle_subscription_id,
            "email": license_obj.email,
            "status": license_obj.status,
            "allowed_containers": license_obj.allowed_containers,
            "current_usage": current_usage,
            "machine_bindings_count": machine_bindings_count,
            "created_at": license_obj.created_at.isoformat(),
            "updated_at": license_obj.updated_at.isoformat(),
        },
        "usage": [
            {
                "id": usage.id,
                "machine_id": usage.machine_id,
                "container_id": usage.container_id,
                "created_at": usage.created_at.isoformat(),
            }
            for usage in usage_list
        ],
        "machine_bindings": [
            {
                "id": binding.id,
                "machine_id": binding.machine_id,
                "created_at": binding.created_at.isoformat(),
            }
            for binding in machine_bindings
        ],
    }



