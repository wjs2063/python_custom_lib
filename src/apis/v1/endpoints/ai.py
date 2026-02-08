from fastapi import APIRouter
from ai.plan_and_execute.pae_agent import workflow

router = APIRouter()



@router.post("/chat")
async def chat(query:str, recursion_limit:int=20):
    graph = workflow.compile()
    config = {"recursion_limit": recursion_limit}
    response = await graph.ainvoke({"input":query},config=config)
    print(response)
    return response
