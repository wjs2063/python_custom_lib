import operator
from typing import Annotated, List, Tuple, TypedDict, Union, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from shared.infra.wrapper.aiohttp_wrapper import get_http_client
from handler.naver.map_handler import get_naver_map_client,get_naver_search_client
from handler.wikipedia.handler import WikipediaHandler


@tool
async def search_naver_local(query: str, display: int = 5):
    """네이버 지역 검색을 통해 맛집이나 장소 정보를 가져옵니다."""
    client = get_naver_search_client()
    return await client.search_local(query=query, display=display)

@tool
async def get_lat_lng(address: str):
    """주소 문자열을 위도(lat)와 경도(lng) 좌표로 변환합니다."""
    client = get_naver_map_client()
    return await client.get_coordinates(address)

@tool
async def search_wikipedia(query: str):
    """위키피디아에서 해당 키워드에 대한 상세 정보를 한국어/영어 버전으로 검색합니다."""
    # Depends를 사용할 수 없는 환경이므로 직접 생성 (실제 구현 시 context에 맞춰 주입)
    client = get_http_client()
    handler = WikipediaHandler(client)
    return await handler.search_global(query)

tools = [search_naver_local, get_lat_lng, search_wikipedia]
llm = ChatOpenAI(model="gpt-4o", temperature=0)
agent_executor = create_react_agent(llm, tools)


class SelfReflectionState(TypedDict):
    input: str
    search_queries: List[str]            # 다음 루프에서 검색할 키워드들
    results: Annotated[List[str], operator.add]  # 누적된 검색 결과
    is_sufficient: bool                  # 정보 충분성 여부
    critique: str                        # 피드백 내용
    response: str                        # 최종 답변
    retry_count: int                     # 루프 횟수 제어

class Grade(BaseModel):
    is_sufficient: bool = Field(description="정보가 충분한지 여부")
    critique: str = Field(description="부족한 점이나 개선해야 할 점에 대한 피드백")
    next_queries: List[str] = Field(description="추가로 검색이 필요한 키워드들 (충분하면 빈 리스트)")


# 1. Researcher Node: 수집된 쿼리를 기반으로 도구 실행
async def research_node(state: SelfReflectionState):
    queries = state.get("search_queries")

    # 초기 진입 시 사용자 질문을 첫 번째 쿼리로 사용
    if not queries:
        queries = [state["input"]]

    new_results = []
    for query in queries:
        # Re-act 에이전트를 써도 되지만, 여기선 도구를 직접 호출하는 방식 예시
        # tools = [search_naver_local, get_lat_lng, search_wikipedia]
        # 실제 환경에선 ToolNode를 쓰거나 직접 호출 로직을 넣습니다.
        search_prompt = f"""당신은 정보 수집 전문가입니다. 다음 작업에 집중하세요:
        1. **정확성**: 장소의 정확한 명칭과 주소를 확인하세요.
        2. **좌표 정보**: 주소가 확인되면 반드시 위도와 경도 좌표를 추출하세요.
        3. **배경 지식**: 위키피디아 등을 통해 해당 장소나 지역의 역사적/문화적 맥락을 확보하세요.

        검색어: {query}"""
        res = await agent_executor.ainvoke({"messages": [HumanMessage(
            content=search_prompt)]})
        new_results.append(f"Query: {query}\nResult: {res['messages'][-1].content}")

    return {"results": new_results, "search_queries": []}

# 2. Grader Node (성찰 노드): 수집된 데이터 검증
async def grade_node(state: SelfReflectionState):
    prompt = f"""당신은 데이터의 완전성을 검증하는 '품질 보증(QA) 전문가'입니다.
    사용자의 질문과 현재까지 수집된 데이터를 비교하여 '합격(Sufficient)' 또는 '보완(Insufficient)' 판정을 내리세요.

    [검토 대상]
    - 사용자 질문: {state['input']}
    - 현재 데이터:
    {chr(10).join(state['results'])}

    [검토 체크리스트 - 모든 항목을 만족해야 Sufficient입니다]
    1. (정보의 구체성): 맛집이나 장소의 이름, 특징이 명확히 기술되었는가?
    2. (지리 데이터): 해당 장소들의 위도(lat)와 경도(lng) 좌표가 모두 포함되었는가?
    3. (심층 정보): 장소의 유래나 역사적 배경 등 '검색 이상의 가치'가 있는 정보가 포함되었는가?
    4. (정확성): 수집된 정보들 사이에 모순은 없는가?

    [결과 작성 가이드]
    - 충분하지 않다면, '어떤 도구'를 사용해서 '무엇'을 더 찾아야 할지 비판(Critique)하고 구체적인 검색어를 제안하세요.
    """

    grader = llm.with_structured_output(Grade)
    result = await grader.ainvoke(prompt)

    return {
        "is_sufficient": result.is_sufficient,
        "critique": result.critique,
        "search_queries": result.next_queries,
        "retry_count": state.get("retry_count", 0) + 1
    }

# 3. Generator Node: 최종 답변 작성
async def generate_node(state: SelfReflectionState):
    prompt = f"""질문: {state['input']}
        수집된 정보: {state['results']}
        피드백 반영: {state['critique']}

위 정보를 종합하여 사용자에게 친절하고 상세한 답변을 작성해 주세요."""

    res = await llm.ainvoke(prompt)
    return {"response": res.content}


def decide_next_step(state: SelfReflectionState):
    # 최대 3번까지만 리트라이 허용 (무한 루프 방지)
    if state["is_sufficient"] or state["retry_count"] >= 3:
        return "generator"
    return "researcher"

workflow = StateGraph(SelfReflectionState)

workflow.add_node("researcher", research_node)
workflow.add_node("grader", grade_node)
workflow.add_node("generator", generate_node)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "grader")

workflow.add_conditional_edges(
    "grader",
    decide_next_step,
    {
        "generator": "generator",
        "researcher": "researcher"
    }
)
workflow.add_edge("generator", END)

