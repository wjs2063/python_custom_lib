from fastapi import APIRouter
from ai_agent.plan_and_execute.pae_agent import (workflow as
                                                 plan_and_execute_workflow)
from ai_agent.self_reflection.reflection import workflow as reflection_workflow

router = APIRouter()



@router.post("/plan-and-execute")
async def chat(query:str, recursion_limit:int=20):
    graph = plan_and_execute_workflow.compile()
    config = {"recursion_limit": recursion_limit}
    response = await graph.ainvoke({"input":query},config=config)
    return response


@router.post("/reflection")
async def reflection_chat(query:str, recursion_limit:int=20):
    graph = reflection_workflow.compile()
    config = {"recursion_limit": recursion_limit}
    response = await graph.ainvoke({"input":query},config=config)
    return response