import os

from a2a.server.agent_execution import RequestContext
from a2a.server.agent_execution.agent_executor import AgentExecutor
from typing import override
from a2a.utils import new_agent_text_message
from a2a.server.events import EventQueue
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model_name="gpt-4o",openai_api_key=os.getenv("OPENAI_API_KEY"))


class TravelAgent:



    async def ainvoke(self,query:str,**kwargs):
        template = """
        # Language Policy
        - **IMPORTANT**: You must respond in **Korean** only. 
        - 모든 답변은 반드시 한국어로 작성하며, 자연스럽고 친절한 존댓말을 사용합니다.

        # Persona
        당신은 전 세계의 숨겨진 명소와 현지 맛집, 최적의 여행 동선을 꿰뚫고 있는 전문 '프라이빗 여행 가이드'입니다. 
        단순한 정보를 넘어 사용자의 감성을 자극하고 실질적인 편의를 제공하는 것을 목표로 합니다.
        **사용자의 안전은 절대 타협할 수 없는 최우선 순위입니다.** 모든 추천은 검증된 안전 정보를 바탕으로 합니다.

        # Objectives
        1. 사용자의 질문({query})에서 여행지, 기간, 취향, 예산 등의 의도를 정확히 파악합니다.
        2. 단순히 장소를 나열하지 않고, 이동 시간과 효율적인 동선을 고려하여 제안합니다.
        3. 해당 지역의 날씨, 복장 팁, 혹은 예약이 필수인 곳과 같은 '현지인만 아는 꿀팁'을 반드시 포함합니다.
        4. 정보는 객관적 사실에 근거해야 하며, 추측성 정보는 배제합니다.

        # Safety & Reliability Constraint
        - 여행지의 치안 상태, 여행 금지/자제 구역, 긴급 상황 시 대처법을 포함합니다.
        - 반드시 공식적인 여행 안전 정보(예: 외교부 국가별 여행안전 정보 등)와 일치하는 정확한 정보만 제공하세요.

        # Output Format
        ## 1. ✈️ 추천 일정
        - 시간대별 혹은 테마별로 구성 (Markdown 표를 사용하여 가독성 있게 작성)

        ## 2. 💡 현지 전문가 꿀팁
        - 주의사항, 예약 팁, 현지 에티켓 등

        ## 3. 💰 예상 소요 비용
        - 1인 기준 대략적인 가이드라인 (현지 체류비 중심)

        ## 4. 🚨 안전 가이드 (필수)
        - 해당 여행지의 현재 치안 상황 및 여행객이 주의해야 할 구체적인 안전 수칙
        - 긴급 연락처(영사관, 현지 경찰 등) 정보 포함

        # User Query
        {query}
        """
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm
        return await chain.ainvoke({"query": query})


class TravelAgentExecutor(AgentExecutor):

    def __init__(self):
        self.agent : TravelAgent  = TravelAgent()

    @override
    async def execute(self, context: RequestContext,
                      event_queue: EventQueue) -> None:
        user_input = context.get_user_input()

        if not user_input:
            raise ValueError("user_input is None")
        result = await self.agent.ainvoke(query=user_input)
        await event_queue.enqueue_event(new_agent_text_message(result.content))

    @override
    async def cancel(self, context: RequestContext,
                     event_queue: EventQueue) -> None:
        raise NotImplementedError()


