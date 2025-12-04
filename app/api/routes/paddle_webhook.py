# app/api/routes/paddle_webhook.py

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import json

from app.core.config import PLAN_MAX_CONTAINERS
from app.core.paddle_webhook_verify import verify_paddle_signature
from app.db.session import get_db
from app.models.customer import Customer
from app.models.license import License
from app.models.webhook_log import WebhookLog

router = APIRouter()


@router.post("/webhook")
async def paddle_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Paddle webhook events.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Success response
    """

    # ------------------------------------------------------------------
    # 1) Verify signature and read raw body (Paddle Webhook v2 JSON)
    # ------------------------------------------------------------------
    # verify_paddle_signature 는 내부에서 header/secret 검증 후
    # 유효하면 raw body bytes 를 그대로 반환한다고 가정
    try:
        body_bytes = await verify_paddle_signature(request)
    except HTTPException:
        # 시그니처 검증 실패는 그대로 예외를 올려서 400 반환
        # (Paddle 쪽에 'invalid signature' 를 알려 주고 재시도 유도)
        raise

    # Get signature from header for logging (support both cases)
    paddle_signature = (
        request.headers.get("Paddle-Signature")
        or request.headers.get("paddle-signature")
        or ""
    )

    # ------------------------------------------------------------------
    # 2) Parse JSON payload (Webhook v2는 JSON 포맷)
    # ------------------------------------------------------------------
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except json.JSONDecodeError:
        # JSON 파싱이 안 되면 로그만 남기고 요청은 성공으로 처리
        # (계속 400을 던지면 Paddle이 무한 재시도 → 로그 폭주 가능)
        webhook_log = WebhookLog(
            event_type="invalid_json",
            payload=body_bytes.decode("utf-8", errors="replace"),
            signature=paddle_signature,
        )
        db.add(webhook_log)
        db.commit()
        return {
            "status": "ignored",
            "reason": "invalid_json",
        }

    # event_type 정규화
    raw_event_type = payload.get("event_type") or payload.get("event") or "unknown"
    event_type = str(raw_event_type).lower()

    # ------------------------------------------------------------------
    # 3) 기본 Webhook 로그 기록
    # ------------------------------------------------------------------
    webhook_log = WebhookLog(
        event_type=event_type,
        payload=json.dumps(payload),
        signature=paddle_signature,
    )
    db.add(webhook_log)

    # ------------------------------------------------------------------
    # 4) 이벤트 타입별 처리
    # ------------------------------------------------------------------
    # Paddle v2 subscription events (예: subscription.created, subscription.updated)
    if event_type in {"subscription.created", "subscription.updated"}:
        subscription_data = payload.get("data", {}) or {}
        subscription_id = subscription_data.get("id")

        if subscription_id:
            # -----------------------------
            # 4-1) 고객 정보 추출 및 저장
            # -----------------------------
            customer_data = subscription_data.get("customer", {}) or {}
            customer_email = customer_data.get("email") or ""
            paddle_customer_id = customer_data.get("id")

            # -----------------------------
            # 4-2) 플랜/상품 정보 추출
            # -----------------------------
            items = subscription_data.get("items", []) or []
            plan_name = "basic"  # default

            if items:
                first_item = items[0] or {}
                price_info = first_item.get("price", {}) or {}

                # 우선 price.name 사용, 없으면 product_id 기반으로 매핑하는 구조로 확장 가능
                raw_plan_name = price_info.get("name") or price_info.get("product_id") or "basic"
                plan_name = str(raw_plan_name).lower()

            # 플랜에 따른 컨테이너 허용 수
            allowed_containers = PLAN_MAX_CONTAINERS.get(plan_name, 1)

            # -----------------------------
            # 4-3) Customer 찾거나 생성
            # -----------------------------
            customer = None
            if customer_email:
                customer = (
                    db.query(Customer)
                    .filter(Customer.email == customer_email)
                    .first()
                )

                if not customer:
                    customer = Customer(
                        email=customer_email,
                        paddle_customer_id=str(paddle_customer_id)
                        if paddle_customer_id
                        else None,
                    )
                    db.add(customer)
                    db.flush()  # customer.id 확보

            # -----------------------------
            # 4-4) License 찾거나 생성/업데이트
            # -----------------------------
            license_obj = (
                db.query(License)
                .filter(License.paddle_subscription_id == str(subscription_id))
                .first()
            )

            if not license_obj:
                license_obj = License(
                    paddle_subscription_id=str(subscription_id),
                    email=customer_email,
                    allowed_containers=allowed_containers,
                    customer_id=customer.id if customer else None,
                    status=subscription_data.get("status", "active"),
                )
                db.add(license_obj)
            else:
                # 기존 라이선스 정보 업데이트
                subscription_status = subscription_data.get("status", "active")
                license_obj.status = subscription_status
                license_obj.email = customer_email
                license_obj.allowed_containers = allowed_containers

                if customer:
                    license_obj.customer_id = customer.id

                license_obj.updated_at = datetime.utcnow()

    elif event_type == "subscription.cancelled":
        # 구독 취소 → 라이선스 상태를 cancelled로 변경
        subscription_data = payload.get("data", {}) or {}
        subscription_id = subscription_data.get("id")

        if subscription_id:
            license_obj = (
                db.query(License)
                .filter(License.paddle_subscription_id == str(subscription_id))
                .first()
            )
            if license_obj:
                license_obj.status = "cancelled"
                license_obj.updated_at = datetime.utcnow()

    # 다른 event_type 은 일단 로그만 쌓고 패스
    # ex) "transaction.completed", "subscription.past_due" 등

    # ------------------------------------------------------------------
    # 5) DB 반영
    # ------------------------------------------------------------------
    db.commit()

    return {"status": "success", "event_type": event_type}
