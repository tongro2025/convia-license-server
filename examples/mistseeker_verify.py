"""
MistSeeker 이미지에서 라이선스 검증을 위한 예제 코드

이 코드는 MistSeeker Docker 이미지나 애플리케이션에서
라이선스 서버에 연결하여 라이선스를 검증하는 방법을 보여줍니다.
"""

import os
import sys
import requests
from typing import Optional, Dict, Any


class LicenseVerifier:
    """라이선스 검증 클라이언트."""

    def __init__(self, license_server_url: str, license_key: str, machine_id: str):
        """라이선스 검증 클라이언트 초기화.

        Args:
            license_server_url: 라이선스 서버 URL (예: https://license.convia.vip)
            license_key: 라이선스 키 (Paddle subscription ID)
            machine_id: 머신 ID (고유한 머신 식별자)
        """
        self.license_server_url = license_server_url.rstrip("/")
        self.license_key = license_key
        self.machine_id = machine_id
        self.verify_endpoint = f"{self.license_server_url}/api/license/verify"

    def get_container_id(self) -> Optional[str]:
        """컨테이너 ID를 가져옵니다.

        Docker 환경에서는 컨테이너 ID를 반환하고,
        일반 환경에서는 None을 반환합니다.

        Returns:
            컨테이너 ID 또는 None
        """
        # Docker 환경에서 컨테이너 ID 가져오기
        try:
            # 방법 1: /etc/hostname 파일 읽기 (Docker 컨테이너)
            with open("/etc/hostname", "r") as f:
                container_id = f.read().strip()
                if container_id:
                    return container_id
        except FileNotFoundError:
            pass

        try:
            # 방법 2: 환경 변수에서 가져오기
            container_id = os.environ.get("HOSTNAME") or os.environ.get("CONTAINER_ID")
            if container_id:
                return container_id
        except Exception:
            pass

        # 방법 3: Docker socket을 통해 가져오기 (고급)
        # docker inspect를 사용할 수 있지만, 여기서는 생략

        return None

    def verify_license(self, container_id: Optional[str] = None) -> Dict[str, Any]:
        """라이선스를 검증합니다.

        Args:
            container_id: 컨테이너 ID (선택적, 제공되지 않으면 자동 감지 시도)

        Returns:
            검증 결과 딕셔너리:
            {
                "valid": bool,
                "message": str,
                "license_id": int (optional),
                "allowed_containers": int (optional),
                "current_usage": int (optional)
            }

        Raises:
            requests.RequestException: 네트워크 오류 발생 시
        """
        # 컨테이너 ID가 제공되지 않으면 자동 감지
        if container_id is None:
            container_id = self.get_container_id()

        # 요청 페이로드 구성
        payload = {
            "license_key": self.license_key,
            "machine_id": self.machine_id,
        }

        if container_id:
            payload["container_id"] = container_id

        try:
            # 라이선스 서버에 검증 요청
            response = requests.post(
                self.verify_endpoint,
                json=payload,
                timeout=10,  # 10초 타임아웃
            )

            # 응답 처리
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "valid": False,
                    "message": f"Server error: {response.status_code}",
                }

        except requests.exceptions.Timeout:
            return {
                "valid": False,
                "message": "License server timeout",
            }
        except requests.exceptions.ConnectionError:
            return {
                "valid": False,
                "message": "Cannot connect to license server",
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"Verification error: {str(e)}",
            }

    def verify_and_exit_on_failure(self, container_id: Optional[str] = None) -> bool:
        """라이선스를 검증하고, 실패 시 프로그램을 종료합니다.

        Args:
            container_id: 컨테이너 ID (선택적)

        Returns:
            검증 성공 시 True, 실패 시 프로그램 종료
        """
        result = self.verify_license(container_id)

        if not result.get("valid", False):
            error_message = result.get("message", "License verification failed")
            print(f"ERROR: {error_message}", file=sys.stderr)
            print(f"License Key: {self.license_key}", file=sys.stderr)
            print(f"Machine ID: {self.machine_id}", file=sys.stderr)
            if container_id:
                print(f"Container ID: {container_id}", file=sys.stderr)

            # 사용량 정보가 있으면 출력
            if "allowed_containers" in result and "current_usage" in result:
                print(
                    f"Usage: {result['current_usage']}/{result['allowed_containers']}",
                    file=sys.stderr,
                )

            sys.exit(1)

        # 성공 시 정보 출력
        print(f"License verified successfully")
        print(f"License ID: {result.get('license_id')}")
        if "allowed_containers" in result:
            print(f"Allowed containers: {result['allowed_containers']}")
        if "current_usage" in result:
            print(f"Current usage: {result['current_usage']}")

        return True


def main():
    """메인 함수 - 예제 사용법."""
    # 환경 변수에서 설정 읽기
    license_server_url = os.environ.get(
        "LICENSE_SERVER_URL", "https://license.convia.vip"
    )
    license_key = os.environ.get("LICENSE_KEY")
    machine_id = os.environ.get("MACHINE_ID", os.environ.get("HOSTNAME", "unknown"))

    if not license_key:
        print("ERROR: LICENSE_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)

    # 검증 클라이언트 생성
    verifier = LicenseVerifier(license_server_url, license_key, machine_id)

    # 라이선스 검증 및 실패 시 종료
    verifier.verify_and_exit_on_failure()


if __name__ == "__main__":
    main()



