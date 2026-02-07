from fastapi import APIRouter,Depends,Query
from handler.sk.tmap_handler import get_tmap_client, TMapClient
from typing import Annotated
router = APIRouter()



@router.post("/pedestrian")
async def get_pedestrian(start_lat : Annotated[float | None, Query(
    description="출발지점의 위도입니다.",example=37.5088)],
    start_lng : Annotated[float | None, Query(
    description="출발지점의 경도입니다.",example=127.0632)],
    end_lat : Annotated[float | None, Query(
    description="도착지점의 위도입니다.",example=37.5088)],
    end_lng : Annotated[float | None, Query(
    description="도착지점의 경도입니다.",example=127.0633)],
    client : TMapClient = Depends(get_tmap_client),):
    """
    SK Map API를 이용하여 출발지점 - 도착지점간의 도보경로를 가져옵니다
    :param start_lat:
    :param start_lng:
    :param end_lat:
    :param end_lng:
    :param client:
    :return:
    """
    return await client.get_pedestrian_route(start_lng,start_lat,end_lng,
                                             end_lat)

