from aiohttp import ClientSession, TCPConnector, BaseConnector
from typing import Protocol
import orjson
from typing import Optional, Any, Dict
import socket


class HTTPClientSessionInterface(Protocol):

    # async def initialize_session(self) -> ClientSession:
    #     """Lifespan 시작 시 호출: 세션 풀 생성"""
    #     pass
    #
    # async def close_session(self) -> None:
    #     pass
    #
    # async def get_session(self) -> ClientSession:
    #     pass

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[dict] = None):
        pass

    async def post(self, url: str, json: Optional[Dict[str, Any]] = None, headers: Optional[dict] = None):
        pass


class AioHttpClient(HTTPClientSessionInterface):
    def __init__(self):
        self._session: Optional[ClientSession] = None

    async def initialize_session(self) -> ClientSession:
        """Lifespan 시작 시 호출: 세션 풀 생성"""
        connector = TCPConnector(
            limit=100,
            ttl_dns_cache=300,
            family=socket.AF_INET,
            enable_cleanup_closed=True
        )
        self._session = ClientSession(
            connector=connector,
            json_serialize=lambda x: orjson.dumps(x).decode("utf-8")
        )

        print("세션 초기화")

    async def close_session(self) -> None:
        """Lifespan 종료 시 호출"""
        if self._session:
            await self._session.close()
        print("세션 종료")

    # --- 공통 요청 처리 메서드 (내부용) ---
    async def _request(self, method: str, url: str, **kwargs) -> Optional[dict]:
        if not self._session:
            raise RuntimeError("Client is not initialized. Check lifespan.")
        print(f"[DEBUG] Session ID: {id(self._session)}")
        # 기본 헤더 설정 (압축 전송 요청)
        headers = kwargs.pop("headers", {}) or {}
        headers.setdefault("Accept-Encoding", "br, gzip, deflate")
        headers.setdefault("Content-Type", "application/json")

        async with self._session.request(method, url, headers=headers, **kwargs) as response:
            response.raise_for_status()  # 4xx, 5xx 에러 발생 시 예외 송출

            # [Performance] bytes로 읽어서 orjson으로 파싱 (Zero-copy 지향)
            raw_bytes = await response.read()
            if not raw_bytes:
                return None
            return orjson.loads(raw_bytes)

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[dict] = None) -> Any:
        return await self._request("GET", url, params=params, headers=headers)

    async def post(self, url: str, json: Optional[Dict[str, Any]] = None, headers: Optional[dict] = None) -> Any:
        # aiohttp의 json= 파라미터는 위에서 설정한 json_serialize(orjson)를 사용함
        return await self._request("POST", url, json=json, headers=headers)



# 싱글톤 인스턴스 (Main에서 사용)
aiohttp_client = AioHttpClient()
