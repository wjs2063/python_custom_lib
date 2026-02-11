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


from fastapi import Request, Response
from starlette.responses import JSONResponse
import uuid

@app.middleware("http")
async def middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    trace_token = trace_id_var.set(trace_id)

    # 1. 요청 바디 읽기
    decoded_body = {}
    body = await request.body()
    # 2. 바디 내용을 로그에 출력 (디코딩 필요 시 .decode() 사용)
    if body:
        decoded_body = body.decode('utf-8')

    # 3. 중요: 소비된 스트림을 재설정 (다음 미들웨어나 엔드포인트에서 읽을 수 있도록)
    async def receive():
        return {"type": "http.request", "body": body}

    # request 객체의 _receive를 가로챔
    request._receive = receive

    try:
        response = await call_next(request)
        return response
    except Exception as e:
        log.error(f"에러 발생 [ID: {trace_id}]: {str(e)}",extra={"body":decoded_body})
        return JSONResponse(
            status_code=500,
            content={"message": "Internal Server Error", "code": 99},
        )
    finally:
        trace_id_var.reset(trace_token)





@app.get("/error")
async def error_handler():
    raise AuthTokenException()


