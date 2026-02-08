from fastapi import FastAPI,Depends,Request,HTTPException
from starlette.responses import JSONResponse

from core.middleware.log_middleware import TraceIDMiddleWare
from contextlib import asynccontextmanager
from shared.infra.wrapper.aiohttp_wrapper import aiohttp_client, AioHttpClient
from core.exceptions import register_application_exception,AuthTokenException, \
    AppBaseException
from shared.utils.logger.root import log
from shared.utils.logger.context import trace_id_var
from apis.router import aggregate_router
import uuid

@asynccontextmanager
async def lifespan(app: FastAPI):
    await aiohttp_client.initialize_session()
    yield
    await aiohttp_client.close_session()


app = FastAPI(title="tutorial", lifespan=lifespan)
app.include_router(aggregate_router)
register_application_exception(app)
#app.add_middleware(TraceIDMiddleWare)


@app.middleware("http")
async def middleware(request: Request,call_next):
    trace_id = str(uuid.uuid4())
    token = trace_id_var.set(trace_id)
    try:
        return await call_next(request)
    except Exception as e:
        log.error(f"에러입니다 : {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": "Internal Server Error", "code": 99},
        )
    finally:
        trace_id_var.reset(token)





@app.get("/error")
async def error_handler():
    raise AuthTokenException()


