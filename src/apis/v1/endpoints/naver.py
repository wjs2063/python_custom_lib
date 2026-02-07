from typing import Annotated

from fastapi import APIRouter,Depends,Query
from handler.naver.map_handler import get_naver_map_client,get_naver_search_client, \
    NaverMapClient

router = APIRouter()





@router.post("/geocode")
async def geocode_handler(query: str,
            coordinate: str | None = None,
            filter_type: str | None = None,
            count: int = 10,
            page: int = 1,client: NaverMapClient = Depends(
    get_naver_map_client),):
    """
    네이버 MAP API를 이용하여 도로명주소로부터 위도/경도 좌표로 변환합니다
    :param query:
    :param coordinate:
    :param filter_type:
    :param count:
    :param page:
    :param client:
    :return:
    """
    return await client.geocode(query, coordinate, filter_type, count)

@router.post("/reverse-geocode")
async def reverse_geocode_handler(lat: Annotated[float,Query(description="위도")],
            lng: Annotated[float,Query(description="경도")],
            orders: Annotated[str,Query(description="주소 타입")] = "legalcode,admcode,addr,roadaddr",
                                  client : NaverMapClient = Depends(
    get_naver_map_client)):
    """
    네이버 MAP API를 이용하여 위도/경도 좌표로부터 주소명을 가져옵니다
    :param lat:
    :param lng:
    :param orders:
    :param client:
    :return:
    """

    return await client.reverse_geocode(lat, lng, orders)