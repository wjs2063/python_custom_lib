from fastapi import FastAPI,Depends
from contextlib import asynccontextmanager
from shared.infra.wrapper.aiohttp_wrapper import aiohttp_client, AioHttpClient
from core.exceptions import register_application_exception, AuthTokenException
from handler.wikipedia.handler import WikipediaHandler
from shared.utils.logger.root import log
@asynccontextmanager
async def lifespan(app: FastAPI):
    await aiohttp_client.initialize_session()
    yield
    await aiohttp_client.close_session()


app = FastAPI(title="tutorial", lifespan=lifespan)

register_application_exception(app)

# 2. 의존성 주입 Getter
async def get_http_client() -> AioHttpClient:
    return aiohttp_client


@app.get("/error")
async def error_handler():
    raise AuthTokenException()


@app.get("/proxy/wiki")
async def get_wiki(
        client: AioHttpClient= Depends(get_http_client)
):
    url = "https://en.wikipedia.org/w/api.php"
    params = {"action": "query", "format": "json", "titles": "Python"}

    # orjson으로 파싱된 dict 반환
    return await client.get(url, params=params)



async def get_wiki_handler(
    client: AioHttpClient = Depends(get_http_client)
) -> WikipediaHandler:
    return WikipediaHandler(client)
# 3. 엔드포인트 구현
@app.get("/wiki/global/{query}")
async def search_global_wiki(
    query: str,
    handler: WikipediaHandler = Depends(get_wiki_handler)
):
    """
    Example: /wiki/global/Samsung
    Result: {"ko": "삼성전자는...", "en": "Samsung Electronics is..."}
    """
    log.info(f"query: {query}, 안녕")
    response = await handler.search_global(query)
    return response