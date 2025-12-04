# Convia License Server – 개발자 가이드

FastAPI 기반 라이선스 서버의 개발 환경 구성 / 필수 파일 / 실행 절차를 한 번에 정리한 문서입니다.

## 1. 프로젝트 개요

Convia License Server는 MistSeeker Pro를 위한 백엔드 라이선스 서버입니다.

- Paddle 결제 시스템과 연동
- 라이선스 발급/검증
- 매직 링크 기반 라이선스 조회/활성화
- 머신 바인딩(컨테이너/머신 ID 제한)
- Webhook 로그 및 라이선스 관리용 Admin API 제공

이 문서는 개발자가 로컬에서 서버를 실행하고, 개발/테스트를 할 수 있게 하는 것을 목표로 합니다.

## 2. 디렉터리 구조 및 필수 파일

### 2.1 루트 디렉터리 구조

```
convia-license-server/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── db/
│   ├── models/
│   └── schemas/
├── scripts/
├── tests/
├── pyproject.toml
├── README.md
├── .env.example
├── .env              # (개발용 로컬에서만, git ignore)
├── .gitignore
├── Dockerfile
└── docker-compose.dev.yml (옵션)
```

### 2.2 app/ 내부 구조 및 역할

#### 1) app/main.py

- FastAPI 앱 엔트리포인트
- 라우터 등록, 미들웨어 설정, 이벤트 훅(startup/shutdown) 등

현재 구조:
```python
from fastapi import FastAPI
from app.api.routes import (
    admin_license,
    admin_webhook,
    paddle_webhook,
    public_license,
)

app = FastAPI(title="Convia License Server")

app.include_router(public_license.router, prefix="/api/license", tags=["license"])
app.include_router(paddle_webhook.router, prefix="/api/paddle", tags=["paddle"])
app.include_router(admin_license.router, prefix="/api/admin/licenses", tags=["admin"])
app.include_router(admin_webhook.router, prefix="/api/admin/webhooks", tags=["admin"])
```

#### 2) app/core/

공통 설정 / 유틸리티 / 보안 관련 코드

필수 파일:

- **app/core/config.py**
  - Pydantic BaseSettings 기반 설정 로딩
  - .env에서 환경변수 로딩
  - `DATABASE_URL`, `PADDLE_WEBHOOK_SECRET`, `ADMIN_API_KEY`, `LICENSE_JWT_SECRET` 등 정의

- **app/core/security.py**
  - Admin API Key 검증 데코레이터/의존성
  - Paddle webhook 시그니처 검증 유틸리티

- **app/core/paddle_webhook_verify.py**
  - Paddle Webhook v2 시그니처 검증 함수

- **app/core/email.py**
  - 매직 링크 이메일 발송 함수 (placeholder)

- **app/core/utils.py**
  - 매직 토큰 생성, 만료 시간 계산 등 유틸리티 함수

#### 3) app/db/

DB 세션 및 베이스 모델, 초기화 관련 코드

필수 파일:

- **app/db/session.py**
  - SQLAlchemy SessionLocal, engine 생성
  - `get_db()` 의존성 함수

- **app/db/base.py**
  - Base 메타클래스 (declarative_base)

#### 4) app/models/

SQLAlchemy 모델 정의

필수 모델:

- **license.py**
  - License 모델: 라이선스 키, 이메일, plan, 컨테이너 제한, 생성일, 만료일 등

- **customer.py**
  - Customer 모델: 고객 이메일, Paddle 고객 ID 등

- **machine_binding.py**
  - MachineBinding 모델: 라이선스 키별 머신/컨테이너 ID 기록

- **magic_token.py**
  - MagicToken 모델: 매직 링크 토큰, 만료 시간, 사용 여부 등

- **license_usage.py**
  - LicenseUsage 모델: 컨테이너 사용량 추적

- **webhook_log.py**
  - WebhookLog 모델: Paddle에서 받은 raw payload, 처리 결과, timestamp

#### 5) app/schemas/

Pydantic 스키마 (입출력 정의)

필수 스키마:

- **license.py**
  - LicenseVerifyRequest
  - LicenseVerifyResponse
  - LicenseOut

- **magic_token.py**
  - MagicLinkRequest
  - MagicLinkClaimResponse

- **machine_binding.py**
  - MachineBinding 관련 스키마

- **webhook_log.py**
  - WebhookLog 관련 스키마

#### 6) app/api/routes/

실제 API 엔드포인트 정의

필수 라우터:

- **public_license.py**
  - `POST /api/license/verify`: 라이선스 검증
  - `POST /api/license/request-magic-link`: 매직 링크 요청
  - `GET /api/license/claim`: 매직 링크를 통한 라이선스 활성화
  - `GET /api/license/magic-link/verify`: 매직 링크 토큰 검증

- **paddle_webhook.py**
  - `POST /api/paddle/webhook`: Paddle 결제/구독 이벤트 수신

- **admin_license.py**
  - `GET /api/admin/licenses`: 라이선스 목록 조회
  - `GET /api/admin/licenses/{id}`: 특정 라이선스 조회
  - `POST /api/admin/licenses/{id}/reset-machines`: 머신 바인딩 리셋

- **admin_webhook.py**
  - `GET /api/admin/webhooks`: Webhook 로그 조회

- **main.py** (health check)
  - `GET /health`: 헬스 체크용

### 2.3 scripts/ 디렉터리

개발/운영 편의 스크립트 모음

필수 스크립트:

- **scripts/init_db.py**
  - DB 연결 후 테이블 생성
  - 로컬 개발용 초기화에 사용

### 2.4 테스트 디렉터리

- **tests/**
  - `tests/test_healthcheck.py`: 헬스 체크 테스트
  - `tests/test_license_verify.py`: 라이선스 검증 테스트
  - `tests/test_paddle_webhook.py`: Paddle webhook 테스트
  - `pytest.ini` 또는 `pyproject.toml` 내 pytest 설정

### 2.5 루트 설정 파일

- **pyproject.toml**
  - 프로젝트 메타 정보
  - 패키지 의존성 (FastAPI, Uvicorn, SQLAlchemy, Pydantic, psycopg[binary], etc.)
  - 개발 의존성 (pytest 등)

- **README.md**
  - 간단한 개요, 로컬 실행법

- **.gitignore**
  - `venv/`, `.env`, `__pycache__/`, `.pytest_cache/`, `*.pyc` 등

- **Dockerfile**
  - 컨테이너 빌드 정의

- **docker-compose.dev.yml** (선택)
  - 로컬용 Postgres + license-server 동시에 띄우는 용도

## 3. 개발 환경 설정

### 3.1 요구 사항

- OS: Ubuntu / macOS / WSL2 등
- Python: 3.10
- DB: PostgreSQL (로컬 or Docker)
- 패키지 매니저: pip or pipx
- (옵션) Docker / Docker Compose

### 3.2 Python 가상환경 생성

```bash
cd /srv/license-server  # 혹은 로컬 경로
python3.10 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3.3 패키지 설치

```bash
pip install --upgrade pip
pip install -e .          # 개발 모드 설치
```

## 4. 환경 변수 및 .env 설정

### 4.1 .env.example

레포에는 샘플 설정 파일인 `.env.example`를 둡니다.

예시:
```bash
# 공통
APP_ENV=dev

# DB 설정 (개발용)
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/convia_license_dev

# Paddle Webhook(샌드박스용) 시크릿
PADDLE_WEBHOOK_SECRET=change_me_paddle_secret

# Admin API
ADMIN_API_KEY=change_me_admin_key

# JWT
LICENSE_JWT_SECRET=change_me_jwt_secret
```

⚠️ 주의: 실제 프로덕션 값은 절대 `.env.example`나 Git에 올리지 않는다.

### 4.2 로컬 개발용 .env 생성

```bash
cp .env.example .env
nano .env
```

- DB를 로컬 PostgreSQL 도커 컨테이너에 맞게 수정
- Sandbox Paddle Webhook Secret 설정
- Admin API Key 임의 문자열로 설정

예시:
```bash
APP_ENV=dev
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/convia_license_dev
PADDLE_WEBHOOK_SECRET=dev_sandbox_secret
ADMIN_API_KEY=dev_admin_key
LICENSE_JWT_SECRET=dev_jwt_secret
```

### 4.3 프로덕션용 .env.production 가이드 (서버 전용, Git에 올리지 않음)

서버(EC2)에서는 `/srv/license-server/.env`에 prod 설정 저장

예시:
```bash
APP_ENV=prod
DATABASE_URL=postgresql://USER:PASS@RDS-ENDPOINT:5432/DBNAME
PADDLE_WEBHOOK_SECRET=prod_real_secret_from_paddle
ADMIN_API_KEY=prod_admin_key_very_secret
LICENSE_JWT_SECRET=prod_jwt_secret_very_secret
```

이 파일은 EC2 안에서만 존재하고, Git 레포에는 절대 포함하지 않는다.

## 5. 로컬 개발 환경에서 DB 구성

### 5.1 Docker로 PostgreSQL 실행 예시

`docker-compose.dev.yml` 예시:

```yaml
version: "3.8"

services:
  db:
    image: postgres:15
    container_name: convia-license-db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: convia_license_dev
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
```

실행:
```bash
docker compose -f docker-compose.dev.yml up -d
```

### 5.2 DB 초기화

```bash
source venv/bin/activate
python scripts/init_db.py
```

`init_db.py` 내용은 대략:
```python
from app.db.base import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)
```

## 6. 서버 실행 (개발 모드)

### 6.1 Uvicorn로 개발 서버 실행

```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

- 기본 포트: http://localhost:8000
- API 문서: http://localhost:8000/docs
- `--reload` 옵션으로 코드 변경 시 자동 반영

## 7. API 요약 (개발 확인용)

### 7.1 Public APIs

- **POST /api/license/verify**
  - 요청: 라이선스 키, 머신 ID, 컨테이너 ID (선택)
  - 응답: 유효 여부, plan, 남은 컨테이너 수 등

- **POST /api/license/request-magic-link**
  - 이메일 입력 → 매직 링크 발송 요청

- **GET /api/license/claim**
  - 매직 링크 토큰으로 라이선스 조회/활성화

- **GET /api/license/magic-link/verify**
  - 매직 링크 토큰 검증 및 라이선스 정보 반환

### 7.2 Paddle Webhook

- **POST /api/paddle/webhook**
  - Paddle이 결제/구독 이벤트를 보내는 엔드포인트
  - 개발 시에는 샌드박스 모드 사용
  - raw payload를 로그/DB에 저장 후, 라이선스 자동 발급 로직 적용

### 7.3 Admin APIs

- **GET /api/admin/licenses**: 라이선스 목록 조회
- **GET /api/admin/licenses/{id}**: 특정 라이선스 조회
- **POST /api/admin/licenses/{id}/reset-machines**: 머신 바인딩 리셋
- **GET /api/admin/webhooks**: Webhook 로그 조회

헤더에 `X-Admin-API-Key: <ADMIN_API_KEY>` 필요.

### 7.4 Health Check

- **GET /health**: 서버 상태 확인

## 8. 테스트 실행

### 8.1 pytest 실행

```bash
source venv/bin/activate
pytest tests/
```

필요 시 `TEST_DATABASE_URL` 환경변수로 테스트용 DB 분리

## 9. 프로덕션 실행 개요 (요약)

### 9.1 Gunicorn + systemd (예시)

`/etc/systemd/system/convia-license.service` 예시:

```ini
[Unit]
Description=Convia License Server
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/srv/license-server
EnvironmentFile=/srv/license-server/.env
ExecStart=/srv/license-server/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
Restart=always

[Install]
WantedBy=multi-user.target
```

적용:
```bash
sudo systemctl daemon-reload
sudo systemctl enable convia-license.service
sudo systemctl start convia-license.service
sudo journalctl -u convia-license.service -f
```

## 10. 개발 시 유의사항

1. `.env`에는 개발/샌드박스용 값만 넣고, 실제 프로덕션 시크릿은 서버/CI에서만 관리한다.

2. DB 타입/구조는 prod와 동일하게, 하지만 계정/권한/데이터는 dev/staging 전용으로 분리한다.

3. Paddle Webhook 개발 시:
   - 처음에는 raw payload를 저장 + 항상 200 OK만 보내는 구조로 시작
   - 이후에 처리 로직(라이선스 생성)을 점진적으로 붙인다.

4. AI IDE / Cursor 사용 시:
   - `.cursorignore`에 `.env`, `secrets/` 등 추가
   - `.env`에 진짜 시크릿 넣지 말기

## 11. 추가 리소스

- API 문서: http://localhost:8000/docs (서버 실행 시)
- FastAPI 문서: https://fastapi.tiangolo.com/
- Paddle API 문서: https://developer.paddle.com/
