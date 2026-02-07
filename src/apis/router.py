from fastapi import APIRouter

from .v1.api import aggregate_router



api_router = APIRouter()
api_router.include_router(aggregate_router)
