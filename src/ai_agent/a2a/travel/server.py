from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
import uvicorn
from ai_agent.a2a.travel.agent import TravelAgentExecutor

agent_skill = AgentSkill(
    description="여행가이드를 도와주는 Agent입니다",
    id="travel_agent",
    name="여행자에게 도움을 주는 여행전문 Agent 입니다",
    tags=["travel","travel_safe_guard"],
)

agent_card = AgentCard(
    description="사용자를 도와 안전한 여행가이드 역할을 해줄 Agent입니다",
    name="TraveAgent",
    url='http://localhost:10000/',
    version='1.0.0',
    default_input_modes=['text'],
    default_output_modes=['text'],
    capabilities=AgentCapabilities(streaming=True),
    skills=[agent_skill],  # Only the basic skill for the public card
    supports_authenticated_extended_card=True,
)

request_handler = DefaultRequestHandler(
    agent_executor=TravelAgentExecutor(),
    task_store=InMemoryTaskStore(),
)

server = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

uvicorn.run(server.build(), host='0.0.0.0', port=10000)