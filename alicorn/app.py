import httpx
import inspect
import typing

from .exceptions import HttpException
from .middleware import BaseMiddleware
from .requests import Request
from .responses import Response, FileResponse
from .routing import Router
from .staticfiles import StaticFiles
from .types import Scope, Receive, Send


class Alicorn:
    def __init__(self):
        self.router = Router()
        self.middleware = BaseMiddleware(self)
        self.exception_handler = None

    # NOTE: properties
    @property
    def exception_handler(self) -> callable:
        return self.__exception_handler

    @exception_handler.setter
    def exception_handler(self, exception: callable) -> None:
        self.__exception_handler = exception


    # NOTE: Routing
    def add_route(self, path: str, handler: callable, methods: list = None) -> None:
        self.router.add_route(path, handler, methods)

    def route(self, path: str, methods: list = None) -> callable:
        def wrapper(handler):
            self.add_route(path, handler, methods)
            return handler

        return wrapper

    def mount(self, router: Router, prefix: str = None) -> None:
        # check if its static route
        is_static = isinstance(router, StaticFiles)

        if prefix and is_static:
            # NOTE: because 'prefix' is already defined in static route
            raise ValueError("'prefix' must be None when mounting static routes.")

        self.router.mount(
            router=router,
            prefix=prefix,
            is_static=is_static,
        )


    # NOTE: Handle Request
    async def handle_request(self, request: Request) -> Response:
        route, kwargs = self.router.get_route(request_path=request.path, method=request.method)

        try:
            if route and route.handler is not None:
                handler = route.handler

                if inspect.isclass(handler):
                    handler = getattr(handler(), request.method.lower(), None)
                    if handler is None:
                        raise HttpException(405)
                if not route.is_valid_method(request.method):
                    raise HttpException(405)

                response = await handler(request, **kwargs)
            else:
                # default response when path not found
                raise HttpException(404)
        except Exception as e:
            if self.exception_handler is not None:
                response = self.exception_handler(request, e)
            elif isinstance(e, HttpException) or isinstance(e, HttpException):
                response = e.response
            else:
                raise e
        return response


    # NOTE: Middleware
    def add_middleware(self, middleware_cls: BaseMiddleware) -> None:
        self.middleware.add(middleware_cls)


    # NOTE: Session
    def session(self, base_url="http://testserver") -> httpx.AsyncClient:
        if not hasattr(self, "__session"):
            self.__session = httpx.AsyncClient(app=self, base_url="http://testserver")

        return self.__session


    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.middleware(scope, receive, send)
