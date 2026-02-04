import aiohttp
import asyncio
from typing import Any, Dict, Optional
import ssl
import certifi


class ExternalAPIError(Exception):
    """외부 API 호출 시 발생하는 기본 예외"""

    def __init__(self, service_name: str, status_code: int, detail: str):
        self.service_name = service_name
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{service_name}] {status_code}: {detail}")


class BaseClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            #SSL 컨텍스트 생성: certifi의 인증서 번들을 사용하도록 설정
            ssl_context = ssl.create_default_context(cafile=certifi.where())

            #TCPConnector에 ssl_context 주입
            connector = aiohttp.TCPConnector(ssl=ssl_context)

            self._session = aiohttp.ClientSession(
                base_url=self.base_url,
                timeout=aiohttp.ClientTimeout(total=10),
                connector=connector  # 커넥터 적용
            )
        return self._session

    async def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:

        session = await self._get_session()
        try:
            async with session.request(method, endpoint, **kwargs) as response:
                if response.status >= 400:
                    error_detail = await response.text()
                    raise ExternalAPIError(self.base_url, response.status, error_detail)
                return await response.json()
        except asyncio.TimeoutError:
            raise ExternalAPIError(self.base_url, 408, "Request Timeout")
        except aiohttp.ClientError as e:
            raise ExternalAPIError(self.base_url, 500, str(e))

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()