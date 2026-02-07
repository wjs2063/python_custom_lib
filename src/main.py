from fastapi import FastAPI,Depends
from core.middleware.log_middleware import TraceIDMiddleWare
from contextlib import asynccontextmanager
from shared.infra.wrapper.aiohttp_wrapper import aiohttp_client, AioHttpClient
from core.exceptions import register_application_exception,AuthTokenException
from apis.router import aggregate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await aiohttp_client.initialize_session()
    yield
    await aiohttp_client.close_session()


app = FastAPI(title="tutorial", lifespan=lifespan)
register_application_exception(app)
app.include_router(aggregate_router)
app.add_middleware(TraceIDMiddleWare)



@app.get("/error")
async def error_handler():
    raise AuthTokenException()

@app.get("/undefined-exception")
async def undefined_exception():
    raise Exception()

