# 프로덕션 배포 가이드

Convia License Server를 프로덕션 환경에 배포하는 방법을 안내합니다.

## 1. 서버 준비

### 1.1 요구사항

- Ubuntu 20.04+ 또는 Amazon Linux 2+
- Python 3.10
- PostgreSQL (RDS 권장)
- 최소 2GB RAM, 2 CPU 코어

### 1.2 프로젝트 디렉터리 생성

```bash
sudo mkdir -p /srv/license-server
sudo chown $USER:$USER /srv/license-server
cd /srv/license-server
```

## 2. 코드 배포

### 2.1 Git에서 클론

```bash
git clone https://github.com/tongro2025/convia-license-server.git .
```

또는 기존 디렉터리에 배포:

```bash
cd /srv/license-server
git pull origin main
```

### 2.2 가상환경 생성 및 의존성 설치

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## 3. 환경 변수 설정

### 3.1 .env 파일 생성

```bash
nano /srv/license-server/.env
```

프로덕션 환경 변수 예시:

```bash
# 환경
APP_ENV=prod

# 데이터베이스 (RDS 엔드포인트 사용)
DATABASE_URL=postgresql://USER:PASSWORD@RDS-ENDPOINT:5432/DBNAME

# Paddle Webhook Secret (Paddle 대시보드에서 가져오기)
PADDLE_WEBHOOK_SECRET=pdl_ntfset_xxxxxxxxxxxxx

# Admin API Key (강력한 랜덤 문자열 생성)
ADMIN_API_KEY=prod_admin_key_very_secret_change_this

# JWT Secret (강력한 랜덤 문자열 생성)
LICENSE_JWT_SECRET=prod_jwt_secret_very_secret_change_this
```

⚠️ **중요**: 
- 실제 프로덕션 시크릿은 절대 Git에 커밋하지 않습니다
- `.env` 파일은 `/srv/license-server/.env`에만 존재해야 합니다
- 파일 권한 설정: `chmod 600 /srv/license-server/.env`

### 3.2 시크릿 생성 방법

```bash
# Admin API Key 생성
openssl rand -hex 32

# JWT Secret 생성
openssl rand -hex 32
```

## 4. 데이터베이스 초기화

### 4.1 DB 연결 확인

```bash
source venv/bin/activate
python -c "from app.db.session import engine; engine.connect(); print('DB connection OK')"
```

### 4.2 테이블 생성

```bash
source venv/bin/activate
python scripts/init_db.py
```

## 5. Systemd 서비스 설정

### 5.1 서비스 파일 복사

```bash
sudo cp deployment/convia-license.service /etc/systemd/system/
```

### 5.2 서비스 파일 수정 (필요시)

사용자 이름이나 경로가 다른 경우:

```bash
sudo nano /etc/systemd/system/convia-license.service
```

주요 설정:
- `User`: 서버 사용자 이름 (예: `ubuntu`, `ec2-user`)
- `WorkingDirectory`: 프로젝트 경로 (기본: `/srv/license-server`)
- `EnvironmentFile`: .env 파일 경로
- `ExecStart`: gunicorn 실행 경로

### 5.3 서비스 활성화 및 시작

```bash
# systemd 재로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable convia-license.service

# 서비스 시작
sudo systemctl start convia-license.service

# 서비스 상태 확인
sudo systemctl status convia-license.service
```

## 6. 로그 확인

### 6.1 실시간 로그 확인

```bash
sudo journalctl -u convia-license.service -f
```

### 6.2 최근 로그 확인

```bash
# 최근 100줄
sudo journalctl -u convia-license.service -n 100

# 오늘 로그
sudo journalctl -u convia-license.service --since today

# 특정 시간대 로그
sudo journalctl -u convia-license.service --since "2024-01-01 00:00:00" --until "2024-01-01 23:59:59"
```

## 7. 서비스 관리

### 7.1 서비스 제어

```bash
# 서비스 시작
sudo systemctl start convia-license.service

# 서비스 중지
sudo systemctl stop convia-license.service

# 서비스 재시작
sudo systemctl restart convia-license.service

# 서비스 상태 확인
sudo systemctl status convia-license.service
```

### 7.2 코드 업데이트 후 재시작

```bash
cd /srv/license-server
git pull origin main
source venv/bin/activate
pip install -e .  # 의존성 변경 시
sudo systemctl restart convia-license.service
```

## 8. Nginx 리버스 프록시 설정 (선택)

### 8.1 Nginx 설치

```bash
sudo apt-get update
sudo apt-get install nginx
```

### 8.2 Nginx 설정 파일 생성

```bash
sudo nano /etc/nginx/sites-available/convia-license
```

설정 예시:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 8.3 설정 활성화

```bash
sudo ln -s /etc/nginx/sites-available/convia-license /etc/nginx/sites-enabled/
sudo nginx -t  # 설정 검증
sudo systemctl reload nginx
```

## 9. SSL/TLS 설정 (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 10. 모니터링 및 헬스 체크

### 10.1 헬스 체크 엔드포인트

```bash
curl http://localhost:8000/health
```

응답:
```json
{"status": "healthy"}
```

### 10.2 API 문서 확인

브라우저에서 접속:
```
http://your-domain.com/docs
```

## 11. 트러블슈팅

### 11.1 서비스가 시작되지 않는 경우

```bash
# 서비스 상태 확인
sudo systemctl status convia-license.service

# 상세 로그 확인
sudo journalctl -u convia-license.service -n 50

# .env 파일 확인
cat /srv/license-server/.env

# 가상환경에서 직접 실행 테스트
cd /srv/license-server
source venv/bin/activate
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 11.2 데이터베이스 연결 오류

- RDS 보안 그룹에서 서버 IP 허용 확인
- DATABASE_URL 형식 확인: `postgresql://USER:PASSWORD@HOST:PORT/DBNAME`
- DB 사용자 권한 확인

### 11.3 포트 충돌

다른 포트 사용 시 systemd 서비스 파일 수정:

```ini
ExecStart=/srv/license-server/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

## 12. 보안 체크리스트

- [ ] `.env` 파일 권한: `chmod 600`
- [ ] `.env` 파일이 Git에 포함되지 않았는지 확인
- [ ] 강력한 `ADMIN_API_KEY` 사용
- [ ] 강력한 `LICENSE_JWT_SECRET` 사용
- [ ] RDS 보안 그룹에서 필요한 IP만 허용
- [ ] Nginx에서 불필요한 헤더 노출 방지
- [ ] SSL/TLS 인증서 설정
- [ ] 정기적인 백업 설정

## 13. 백업

### 13.1 데이터베이스 백업

```bash
# RDS 스냅샷 사용 (권장)
# 또는 pg_dump 사용
pg_dump -h RDS-ENDPOINT -U USER -d DBNAME > backup_$(date +%Y%m%d).sql
```

### 13.2 환경 변수 백업

```bash
# 안전한 위치에 암호화하여 저장
sudo cp /srv/license-server/.env /backup/location/.env.encrypted
```

## 14. 업데이트 절차

1. 코드 백업
2. Git에서 최신 코드 가져오기
3. 의존성 업데이트 (필요시)
4. 마이그레이션 실행 (필요시)
5. 서비스 재시작
6. 헬스 체크 확인
7. 로그 모니터링
