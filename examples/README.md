# MistSeeker 라이선스 검증 예제

이 디렉토리에는 MistSeeker 이미지에서 라이선스 검증을 수행하는 예제 코드가 포함되어 있습니다.

## 파일 설명

- `mistseeker_verify.py`: Python 기반 라이선스 검증 클라이언트
- `docker_entrypoint.sh`: Docker 컨테이너용 엔트리포인트 스크립트
- `README.md`: 이 파일

## 사용 방법

### Python 스크립트 사용

```python
from examples.mistseeker_verify import LicenseVerifier

# 검증 클라이언트 생성
verifier = LicenseVerifier(
    license_server_url="https://license.convia.vip",
    license_key="your-license-key",
    machine_id="unique-machine-id"
)

# 라이선스 검증
result = verifier.verify_license()

if result["valid"]:
    print("License is valid!")
    print(f"Allowed containers: {result.get('allowed_containers')}")
    print(f"Current usage: {result.get('current_usage')}")
else:
    print(f"License verification failed: {result['message']}")
    sys.exit(1)
```

### 환경 변수 사용

```bash
export LICENSE_SERVER_URL="https://license.convia.vip"
export LICENSE_KEY="your-license-key"
export MACHINE_ID="unique-machine-id"

python examples/mistseeker_verify.py
```

### Docker 이미지에 통합

#### 방법 1: Python 스크립트 사용

Dockerfile에 추가:

```dockerfile
# 라이선스 검증 스크립트 복사
COPY examples/mistseeker_verify.py /app/verify_license.py

# 엔트리포인트 수정
ENTRYPOINT ["python", "/app/verify_license.py", "&&", "python", "/app/main.py"]
```

또는 Python 코드에서 직접 호출:

```python
import sys
from verify_license import LicenseVerifier

# 애플리케이션 시작 전에 검증
verifier = LicenseVerifier(
    license_server_url=os.environ.get("LICENSE_SERVER_URL", "https://license.convia.vip"),
    license_key=os.environ.get("LICENSE_KEY"),
    machine_id=os.environ.get("MACHINE_ID", os.environ.get("HOSTNAME", "unknown"))
)

if not verifier.verify_and_exit_on_failure():
    sys.exit(1)

# 검증 성공 후 애플리케이션 실행
# ... your application code ...
```

#### 방법 2: Shell 스크립트 사용

Dockerfile에 추가:

```dockerfile
# 라이선스 검증 스크립트 복사
COPY examples/docker_entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 엔트리포인트 설정
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "/app/main.py"]
```

Docker 실행:

```bash
docker run -e LICENSE_KEY="your-license-key" \
           -e LICENSE_SERVER_URL="https://license.convia.vip" \
           -e MACHINE_ID="unique-machine-id" \
           your-image
```

## API 엔드포인트

라이선스 검증 API:

- **URL**: `POST /api/license/verify`
- **Request Body**:
  ```json
  {
    "license_key": "string (required)",
    "machine_id": "string (required)",
    "container_id": "string (optional)"
  }
  ```
- **Response**:
  ```json
  {
    "valid": true,
    "message": "License verified and bound to machine",
    "license_id": 1,
    "allowed_containers": 5,
    "current_usage": 2
  }
  ```

## 주의사항

1. **머신 ID**: 각 머신/컨테이너마다 고유한 ID를 사용해야 합니다.
   - Docker: `hostname` 또는 환경 변수
   - Kubernetes: Pod 이름 또는 Node 이름
   - 일반 서버: 호스트명 또는 UUID

2. **컨테이너 ID**: 컨테이너 환경에서는 컨테이너 ID를 제공하는 것이 좋습니다.
   - Docker: `hostname` 또는 `$HOSTNAME` 환경 변수
   - Kubernetes: Pod 이름

3. **네트워크**: 라이선스 서버에 접근 가능해야 합니다.
   - 방화벽 설정 확인
   - DNS 설정 확인

4. **에러 처리**: 검증 실패 시 애플리케이션을 종료하도록 구현해야 합니다.

## 테스트

로컬에서 테스트:

```bash
# 환경 변수 설정
export LICENSE_SERVER_URL="http://localhost:8000"
export LICENSE_KEY="test-license-key"
export MACHINE_ID="test-machine-1"

# 검증 실행
python examples/mistseeker_verify.py
```

## 문제 해결

### "Cannot connect to license server"
- 라이선스 서버 URL이 올바른지 확인
- 네트워크 연결 확인
- 방화벽 설정 확인

### "License not found"
- 라이선스 키가 올바른지 확인
- 라이선스가 활성 상태인지 확인 (Admin 페이지에서 확인)

### "Container limit reached"
- 허용된 컨테이너 수를 초과했습니다
- Admin 페이지에서 컨테이너 사용량을 리셋하거나
- 사용하지 않는 컨테이너를 종료하세요
