import asyncio
from shared.infra.wrapper.aiohttp_wrapper import AioHttpClient


class WikipediaHandler:

    def __init__(self, http_client: AioHttpClient):
        self._client = http_client

    async def search_global(self, query: str) -> dict[str, str]:
        task_ko = self._fetch_wiki_data(lang="ko", query=query)
        task_en = self._fetch_wiki_data(lang="en", query=query)

        # 2. 병렬 실행 (Total Time = max(ko_time, en_time))
        # 순차 실행 시 sum(ko_time, en_time)이 되므로 gather가 필수적입니다.
        result_ko, result_en = await asyncio.gather(task_ko, task_en)

        return {
            "ko": result_ko,
            "en": result_en
        }

    async def _fetch_wiki_data(self, lang: str, query: str) -> str:
        """특정 언어의 위키피디아에서 요약본 추출"""
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": query,
            "prop": "extracts",
            #"exintro": str(True),  # 도입부만
            "explaintext": str(True)  # HTML 태그 제거 (Plain Text)
        }

        headers = {
            "User-Agent": "MenuAdvisorBot/1.0 (dev_email@example.com)"
        }
        try:
            # 주입받은 최적화 클라이언트 사용
            data = await self._client.get(url,headers=headers, params=params)
            return data
        except Exception as e:
            # 에러 발생 시 전체 로직이 죽지 않고 해당 언어만 에러 메시지 반환
            print(f"Error fetching {lang} wiki: {e}")
            return "Search failed."
