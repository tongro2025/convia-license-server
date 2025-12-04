#!/bin/bash
# MistSeeker Docker 이미지용 엔트리포인트 스크립트
# 라이선스 검증 후 애플리케이션 실행

set -e

# 환경 변수 확인
if [ -z "$LICENSE_KEY" ]; then
    echo "ERROR: LICENSE_KEY environment variable is required" >&2
    exit 1
fi

LICENSE_SERVER_URL="${LICENSE_SERVER_URL:-https://license.convia.vip}"
MACHINE_ID="${MACHINE_ID:-$(hostname)}"
CONTAINER_ID="${CONTAINER_ID:-$(hostname)}"

# 라이선스 검증
echo "Verifying license..."
VERIFY_RESPONSE=$(curl -s -X POST "${LICENSE_SERVER_URL}/api/license/verify" \
    -H "Content-Type: application/json" \
    -d "{
        \"license_key\": \"${LICENSE_KEY}\",
        \"machine_id\": \"${MACHINE_ID}\",
        \"container_id\": \"${CONTAINER_ID}\"
    }")

# 응답 파싱 (jq가 있으면 사용, 없으면 grep 사용)
if command -v jq &> /dev/null; then
    VALID=$(echo "$VERIFY_RESPONSE" | jq -r '.valid')
    MESSAGE=$(echo "$VERIFY_RESPONSE" | jq -r '.message')
else
    # jq가 없으면 간단한 파싱
    VALID=$(echo "$VERIFY_RESPONSE" | grep -o '"valid":[^,]*' | cut -d: -f2 | tr -d ' ')
    MESSAGE=$(echo "$VERIFY_RESPONSE" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
fi

# 검증 실패 시 종료
if [ "$VALID" != "true" ]; then
    echo "ERROR: License verification failed: $MESSAGE" >&2
    echo "License Key: $LICENSE_KEY" >&2
    echo "Machine ID: $MACHINE_ID" >&2
    echo "Container ID: $CONTAINER_ID" >&2
    exit 1
fi

echo "License verified successfully"
echo "$VERIFY_RESPONSE" | jq '.' 2>/dev/null || echo "$VERIFY_RESPONSE"

# 원래 엔트리포인트 실행
exec "$@"


