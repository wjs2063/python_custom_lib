from .endpoints.wikipedia import router as wikipedia_router
from .endpoints.sk import router as sk_router
from .endpoints.naver import router as naver_router
from .endpoints.ai import router as ai_router
from fastapi import APIRouter



aggregate_router = APIRouter()


aggregate_router.include_router(wikipedia_router,prefix="/wikipedia",tags=["wikipedia"])
aggregate_router.include_router(sk_router,prefix="/sk",tags=["sk"])
aggregate_router.include_router(naver_router,prefix="/naver",tags=["naver"])
aggregate_router.include_router(ai_router,prefix="/ai",tags=["ai"])

@aggregate_router.get("/exception")
async def index():
    raise Exception()
