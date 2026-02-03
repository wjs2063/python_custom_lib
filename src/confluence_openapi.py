import os
import json
import requests
from typing import Dict, Any

class ConfluenceClient:
    def __init__(self, domain: str, email: str, token: str):
        self.base_url = f"https://{domain}/wiki/api/v2"
        self.auth = (email, token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def get_page_info(self, page_id: str) -> Dict[str, Any]:
        """페이지의 현재 버전과 정보를 가져옵니다."""
        response = requests.get(
            f"{self.base_url}/pages/{page_id}",
            auth=self.auth,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def update_page_body(self, page_id: str, title: str, html_content: str):
        """페이지 본문을 새로운 내용으로 업데이트합니다."""
        # 1. 현재 버전 확인 (업데이트를 위해 반드시 필요)
        current_info = self.get_page_info(page_id)
        current_version = current_info['version']['number']

        # 2. 업데이트 데이터 구성
        payload = {
            "id": page_id,
            "status": "current",
            "title": title,
            "body": {
                "representation": "storage",  # 컨플루언스 저장 포맷 사용
                "value": html_content
            },
            "version": {
                "number": current_version + 1,
                "message": "API를 통한 자동 문서 업데이트"
            }
        }

        # 3. PUT 요청으로 업데이트 실행
        response = requests.put(
            f"{self.base_url}/pages/{page_id}",
            data=json.dumps(payload),
            auth=self.auth,
            headers=self.headers
        )

        if response.status_code == 200:
            print(f"✅ 페이지 업데이트 성공! (Version: {current_version + 1})")
        else:
            print(f"❌ 실패: {response.status_code}")
            print(response.text)

# --- 실행 예시 ---
if __name__ == "__main__":
    # 환경 변수 또는 직접 입력
    DOMAIN = "your-domain.atlassian.net"
    EMAIL = "your-email@example.com"
    API_TOKEN = "your_api_token_here"
    PAGE_ID = "12345678"  # 업데이트할 페이지 ID

    # 1. OpenAPI 스펙을 읽어오거나 변환된 HTML 생성
    # 여기서는 예시로 ReDoc 스타일로 감싼 내용을 넣습니다.
    new_content = """
    <p>이 문서는 배포 파이프라인에 의해 자동 생성되었습니다.</p>
    <ac:structured-macro ac:name="info" ac:schema-version="1">
        <ac:rich-text-body><p>최신 API 명세는 아래 OpenAPI 매크로를 확인하세요.</p></ac:rich-text-body>
    </ac:structured-macro>
    """

    client = ConfluenceClient(DOMAIN, EMAIL, API_TOKEN)
    client.update_page_body(PAGE_ID, "🚀 API 자동화 문서", new_content)