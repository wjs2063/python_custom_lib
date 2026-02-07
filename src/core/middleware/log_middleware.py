from starlette.types import ASGIApp, Scope, Receive, Send
from fastapi import Request
from core.exceptions import AppBaseException
from shared.utils.logger.context import trace_id_var
from shared.utils.logger.root import log
import uuid


class TraceIDMiddleWare:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        trace_id = str(uuid.uuid4())
        token = trace_id_var.set(trace_id)
        request = Request(scope, receive)
        request.state.trace_id = trace_id
        """
        이렇게 하는 이유는 Exception 객체와 AppBaseException 객체를 처리하는 미들웨어가 달라서 
        context_var가 초기화된다. 
        Exception 이 나면 아래코드의 finally가 먼저 실행후에 -> Exception 처리하는 미들웨어로 간다.
        따라서 context_var가 초기화된후에 log의 TraceFilter가 동작함
        
        그래서 request state에 주입하자
        """
        print("middleware 실행")
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-trace-id", trace_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)

        finally:
            trace_id_var.reset(token)