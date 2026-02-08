from langchain_core.tools import tool
from handler.naver.map_handler import get_naver_map_client,get_naver_search_client
from shared.infra.wrapper.aiohttp_wrapper import aiohttp_client,get_http_client
from handler.wikipedia.handler import WikipediaHandler
from typing import List, Tuple, Optional
import operator
from typing import Annotated, List, TypedDict, Union
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel,Field
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
    client = get_naver_search_client()
    handler = WikipediaHandler(client)
    return await handler.search_global(query)

tools = [search_naver_local, get_lat_lng, search_wikipedia]


class PlanExecuteState(TypedDict):
    input: str
    plan: List[str]
    all_plans : list[str]
    past_steps: Annotated[List[Tuple[str, str]], operator.add]
    response: str


llm = ChatOpenAI(model="gpt-4o", streaming=True)


class Plan(BaseModel):
    """생성할 계획 리스트"""
    steps: List[str] = Field(description="실행해야 할 단계별 작업 목록")

class Response(BaseModel):
    """최종 답변"""
    response: str

class Act(BaseModel):
    """다음 행동 선택"""
    action: Union[Plan, Response] = Field(description="계획을 수정하거나 최종 답변을 하세요.")

# Planner 노드
async def plan_node(state: PlanExecuteState):
    prompt = f"""
    당신은 복합적인 문제를 해결하기 위해 단계별 실행 계획을 수립하는 '전략 분석가'입니다.
    사용자의 질문을 분석하여, 가용 도구를 효율적으로 사용하는 논리적인 계획을 세우세요.

    [가용 도구 리스트]
    1. search_naver_local: 장소명, 맛집, 위치 정보 검색
    2. get_lat_lng: 특정 주소의 위도/경도 좌표 추출
    3. search_wikipedia: 지역의 유래, 역사, 인물 등 백과사전적 정보 검색

    [계획 수립 가이드라인]
    - (의존성 고려): 주소를 먼저 검색한 후, 그 결과로 나온 주소를 바탕으로 좌표를 추출해야 합니다.
    - (구체성): 각 단계는 하나의 명확한 목표를 가져야 합니다.
    - (언어): 모든 계획과 결과물은 반드시 한국어로 작성합니다.
    - (최적화): 중복되는 단계는 피하고, 목적 달성에 필요한 최소한의 경로를 설계하세요.

    사용자 질문: {state['input']}
    
    위 질문을 해결하기 위한 최적의 단계별 계획을 생성하세요.
    """
    planner = llm.with_structured_output(Plan)
    plan = await planner.ainvoke(prompt)
    return {"plan": plan.steps,"all_plans":plan.steps}

# Re-plan 노드 (실행 결과를 보고 다음 결정)

async def replan_node(state: PlanExecuteState):
    prompt = f"""
    당신은 실행 결과를 검토하고 최종 답변을 완성하거나 계획을 수정하는 '품질 관리자'입니다.
    
    [현재 상황]
    - 원래 목표: {state['input']}
    - 남은 계획: {state['plan']}
    - 지금까지의 실행 기록: {state['past_steps']}

    [판단 기준]
    1. **충분성**: 현재까지 수집된 정보가 사용자의 질문에 답변하기에 충분한가?
    2. **정확성**: 도구 실행 결과에서 오류가 발생했거나 정보가 부족하지 않은가?
    3. **연속성**: 남은 계획이 여전히 유효한가? (이미 달성했다면 계획에서 삭제)

    [행동 지침]
    - 모든 정보가 수집되었다면: `Response` 객체를 선택하고, 수집된 모든 정보(맛집 목록, 좌표 정보, 지역 유래 등)를 종합하여 친절하고 가독성 좋은 한국어로 최종 답변을 작성하세요.
    - 정보가 더 필요하다면: `Plan` 객체를 선택하여 현재 상황에 맞게 남은 계획을 수정하거나 새로운 단계를 추가하세요.

    지금까지 얻은 데이터를 바탕으로 최선의 결정을 내리세요.
    """

    replanner = llm.with_structured_output(Act)
    result = await replanner.ainvoke(prompt)

    if isinstance(result.action, Response):
        return {"response": result.action.response}
    else:
        return {"plan": result.action.steps,"all_plans":result.action.steps}


from langgraph.prebuilt import create_react_agent

agent_executor = create_react_agent(llm, tools)

async def execute_node(state: PlanExecuteState):
    task = state["plan"][0] # 첫 번째 단계 실행
    agent_response = await agent_executor.ainvoke({"messages": [("user", task)]})
    output = agent_response["messages"][-1].content
    return {"past_steps": [(task, output)], "plan": state["plan"][1:]}


workflow = StateGraph(PlanExecuteState)

workflow.add_node("planner", plan_node)
workflow.add_node("executor", execute_node)
workflow.add_node("replan", replan_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "replan")

# 리플래너에서 조건부 분기
def should_continue(state: PlanExecuteState):
    if "response" in state and state["response"]:
        return END
    return "executor"

workflow.add_conditional_edges("replan", should_continue)


# 실행 예시
# async def main():
#     inputs = {"input": "성수동 맛집을 검색해서 좌표랑 그 지역의 유래를 알려줘"}
#     async for event in app.astream(inputs):
#         for k, v in event.items():
#             if k != "__metadata__":
#                 print(f"Node: {k}")
#                 print(v)

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())