import typing

from .requests import Request
from .responses import Response
from .types import ASGIApp, Scope, Receive, Send


class Middleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    def add(self, middleware_cls: typing.Type):
        self.app = middleware_cls(self.app)

    async def process_request(self, request: Request):
        pass

    async def process_response(self, request: Request):
        pass

    async def handle_request(self, request: Request) -> Response:
        await self.process_request(request)
        response = await self.app.handle_request(request)
        await self.process_response(request)
        return response

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive)
        response = await self.app.handle_request(request)
        await response(send)
