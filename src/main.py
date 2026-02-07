from fastapi import FastAPI,Depends
from contextlib import asynccontextmanager
from shared.infra.wrapper.aiohttp_wrapper import aiohttp_client, AioHttpClient
from core.exceptions import register_application_exception, AuthTokenException
from apis.router import aggregate_router
from handler.wikipedia.handler import WikipediaHandler,get_http_client
from shared.utils.logger.root import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    await aiohttp_client.initialize_session()
    yield
    await aiohttp_client.close_session()


app = FastAPI(title="tutorial", lifespan=lifespan)

register_application_exception(app)
app.include_router(aggregate_router)




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

