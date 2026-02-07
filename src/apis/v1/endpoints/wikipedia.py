from fastapi import APIRouter,Depends
from handler.wikipedia.handler import WikipediaHandler,get_wiki_handler
from shared.utils.logger.root import log


router = APIRouter()


@router.get("/wiki/global/{query}")
async def search_global_wiki(
    query: str,
    handler: WikipediaHandler = Depends(get_wiki_handler)
):
    """
    Example: /wiki/global/Samsung
    Result: {"ko": "삼성전자는...", "en": "Samsung Electronics is..."}
    """
    log.info(f"query: {query}")
    response = await handler.search_global(query)
    return response