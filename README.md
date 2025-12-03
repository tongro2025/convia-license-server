# Convia License Server

FastAPI 기반 라이선스 서버입니다. Paddle 결제 시스템과 연동하여 라이선스 검증 및 관리를 제공합니다.

## 주요 기능

- 라이선스 검증 API
- 매직 링크를 통한 라이선스 활성화
- 머신 바인딩 관리
- Paddle Webhook 처리
- 관리자 API (라이선스 및 Webhook 로그 조회)

## 로컬 실행

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -e .
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 `.env.example`을 참고하여 값을 채워주세요:

```bash
cp .env.example .env
# .env 파일을 열어 실제 값 입력
```

필수 환경 변수:
- `DATABASE_URL`: PostgreSQL 데이터베이스 연결 URL
- `PADDLE_WEBHOOK_SECRET`: Paddle Webhook 서명 검증용 시크릿
- `ADMIN_API_KEY`: 관리자 API 인증 키
- `LICENSE_JWT_SECRET`: 라이선스 JWT 토큰 생성용 시크릿

### 3. 데이터베이스 초기화

```bash
python scripts/init_db.py
```

### 4. 서버 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn app.main:app --reload

# 프로덕션 모드
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

서버는 기본적으로 `http://localhost:8000`에서 실행됩니다.

API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

## API 엔드포인트

### Public APIs
- `POST /api/license/verify`: 라이선스 검증
- `POST /api/license/request-magic-link`: 매직 링크 요청
- `GET /api/license/claim`: 매직 링크를 통한 라이선스 활성화

### Paddle Webhook
- `POST /api/paddle/webhook`: Paddle 결제/구독 이벤트 수신

### Admin APIs
- `GET /api/admin/licenses`: 라이선스 목록 조회
- `GET /api/admin/licenses/{id}`: 특정 라이선스 조회
- `POST /api/admin/licenses/{id}/reset-machines`: 머신 바인딩 리셋
- `GET /api/admin/webhooks`: Webhook 로그 조회

모든 Admin API는 `X-Admin-API-Key` 헤더에 `ADMIN_API_KEY` 값을 포함해야 합니다.

## 프로젝트 구조

```
convia-license-server/
├── app/
│   ├── api/routes/       # API 라우터
│   ├── core/             # 보안 및 유틸리티
│   ├── db/               # 데이터베이스 설정
│   ├── models/           # SQLAlchemy 모델
│   └── schemas/          # Pydantic 스키마
├── scripts/              # 유틸리티 스크립트
├── tests/                # 테스트
└── pyproject.toml        # 프로젝트 설정
```

## 개발

### 테스트 실행

```bash
pytest tests/
```

## Docker

```bash
# 이미지 빌드
docker build -t convia-license-server .

# 컨테이너 실행
docker run -p 8000:8000 --env-file .env convia-license-server
```

