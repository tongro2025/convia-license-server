# app/api/routes/paddle_webhook.py

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
import json

from app.core.db import get_db
from app.core.paddle_webhook_verify import verify_paddle_signature

router = APIRouter()

@router.post("/webhook")
async def paddle_webhook(request: Request, db: Session = Depends(get_db)):
    # 시그니처 검증 + body 가져오기
    body_bytes = await verify_paddle_signature(request)
    payload = json.loads(body_bytes)

    # 여기서부터는 payload 가지고 라이선스 생성 로직…
    # ...
    return {"status": "ok"}
