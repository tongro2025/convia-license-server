"""Public license API routes."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.email import send_magic_link_email
from app.core.utils import generate_magic_token, get_token_expiry
from app.db.session import get_db
from app.models.license import License
from app.models.license_usage import LicenseUsage
from app.models.machine_binding import MachineBinding
from app.models.magic_token import MagicToken
from app.schemas.license import LicenseVerifyRequest, LicenseVerifyResponse
from app.schemas.magic_token import MagicLinkClaimResponse, MagicLinkRequest

router = APIRouter()


@router.post("/verify", response_model=LicenseVerifyResponse)
async def verify_license(
    request: LicenseVerifyRequest,
    db: Session = Depends(get_db),
):
    """Verify license and bind to machine ID.

    Args:
        request: License verification request
        db: Database session

    Returns:
        License verification response
    """
    # Find license by paddle_subscription_id (used as license_key)
    license_obj = db.query(License).filter(
        License.paddle_subscription_id == request.license_key
    ).first()

    if not license_obj or license_obj.status != "active":
        return LicenseVerifyResponse(
            valid=False,
            message="Invalid or inactive license",
        )

    # Calculate current container usage
    current_usage = db.query(LicenseUsage).filter(
        LicenseUsage.license_id == license_obj.id
    ).count()

    # Check container limit (if allowed_containers is -1, it's unlimited)
    allowed_containers = license_obj.allowed_containers
    if allowed_containers != -1 and current_usage >= allowed_containers:
        return LicenseVerifyResponse(
            valid=False,
            message=f"Container limit reached. Allowed: {allowed_containers}, Current: {current_usage}",
            allowed_containers=allowed_containers,
            current_usage=current_usage,
        )

    # Track container usage if container_id is provided
    if request.container_id:
        # Check if this container is already tracked
        existing_usage = db.query(LicenseUsage).filter(
            LicenseUsage.license_id == license_obj.id,
            LicenseUsage.container_id == request.container_id,
        ).first()

        if not existing_usage:
            usage = LicenseUsage(
                license_id=license_obj.id,
                machine_id=request.machine_id,
                container_id=request.container_id,
            )
            db.add(usage)
            current_usage += 1

    # Check if machine is already bound to this license
    existing_binding = db.query(MachineBinding).filter(
        MachineBinding.license_id == license_obj.id,
        MachineBinding.machine_id == request.machine_id,
    ).first()

    if not existing_binding:
        # Create new machine binding
        binding = MachineBinding(
            license_id=license_obj.id,
            machine_id=request.machine_id,
        )
        db.add(binding)

    db.commit()

    return LicenseVerifyResponse(
        valid=True,
        message="License verified and bound to machine",
        license_id=license_obj.id,
        allowed_containers=allowed_containers,
        current_usage=current_usage,
    )


@router.post("/request-magic-link")
async def request_magic_link(
    request: MagicLinkRequest,
    db: Session = Depends(get_db),
):
    """Request magic link for license activation.

    Args:
        request: Magic link request
        db: Database session

    Returns:
        Success message (email sent)
    """
    license_obj = db.query(License).filter(
        License.paddle_subscription_id == request.license_key
    ).first()

    if not license_obj or license_obj.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found or inactive",
        )

    # Use email from request or license
    email = request.email or license_obj.email
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is required",
        )

    # Generate magic token
    token = generate_magic_token()
    expires_at = get_token_expiry()

    magic_token = MagicToken(
        token=token,
        license_id=license_obj.id,
        expires_at=expires_at,
    )
    db.add(magic_token)
    db.commit()

    # Send magic link email
    send_magic_link_email(
        email=email,
        token=token,
        license_key=request.license_key,
    )

    return {
        "success": True,
        "message": "Magic link sent to email",
        "expires_at": expires_at.isoformat(),
    }


@router.get("/claim", response_model=MagicLinkClaimResponse)
async def claim_license(
    token: str,
    machine_id: str,
    db: Session = Depends(get_db),
):
    """Claim license using magic token.

    Args:
        token: Magic token from link
        machine_id: Machine ID to bind license to
        db: Database session

    Returns:
        License claim response
    """
    magic_token = db.query(MagicToken).filter(
        MagicToken.token == token,
        MagicToken.used_at.is_(None),
        MagicToken.expires_at > datetime.utcnow(),
    ).first()

    if not magic_token:
        return MagicLinkClaimResponse(
            success=False,
            message="Invalid or expired token",
        )

    # Mark token as used
    magic_token.used_at = datetime.utcnow()

    # Create machine binding
    existing_binding = db.query(MachineBinding).filter(
        MachineBinding.license_id == magic_token.license_id,
        MachineBinding.machine_id == machine_id,
    ).first()

    if not existing_binding:
        binding = MachineBinding(
            license_id=magic_token.license_id,
            machine_id=machine_id,
        )
        db.add(binding)

    db.commit()

    return MagicLinkClaimResponse(
        success=True,
        message="License claimed successfully",
        license_id=magic_token.license_id,
    )


@router.get("/magic-link/verify")
async def verify_magic_link(
    token: str,
    db: Session = Depends(get_db),
):
    """Verify magic link token and return license information.

    Args:
        token: Magic token from link
        db: Database session

    Returns:
        License information if token is valid
    """
    magic_token = db.query(MagicToken).filter(
        MagicToken.token == token,
        MagicToken.used_at.is_(None),
        MagicToken.expires_at > datetime.utcnow(),
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

    return {
        "valid": True,
        "license_id": license_obj.id,
        "license_key": license_obj.paddle_subscription_id,
        "email": license_obj.email,
        "status": license_obj.status,
        "allowed_containers": license_obj.allowed_containers,
    }




