"""Admin license API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.core.security import verify_admin_api_key
from app.db.session import get_db
from app.models.license import License
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




