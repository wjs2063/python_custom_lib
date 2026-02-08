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
    당신은 사용자의 의도를 파악하여 답변을해주는 Agent의 계획을 설계하는 전문가입니다. 
    사용자 질문: {state['input']}\n적절한 계획을 세워주세요.
    반드시 한국어로 답변해주세요.
    """
    planner = llm.with_structured_output(Plan)
    plan = await planner.ainvoke(prompt)
    return {"plan": plan.steps,"all_plans":plan.steps}

# Re-plan 노드 (실행 결과를 보고 다음 결정)

async def replan_node(state: PlanExecuteState):
    prompt = f"""사용자 질문: {state['input']}
        현재 계획: {state['plan']}
        실행 기록: {state['past_steps']}
        위 기록을 바탕으로 계획을 업데이트하거나 최종 답변을 작성하세요.
        반드시 한국어로 답변해주세요
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