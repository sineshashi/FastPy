import asyncio
import traceback
import inspect
from typing import Callable, Optional, Dict, Any
from pydantic import BaseModel
from .core import MethodWisePathsInfo, Method
from .requests import Request
from .responses import Response
from .params import HeaderParam, Headers, Body
from .exceptions import HttpException

class FastPy:
    def __init__(self) -> None:
        self._method_wise_path_info = MethodWisePathsInfo()

    def add_api_route(self, method: Method, path: str, handler: Callable) -> None:
        '''Add new API route.'''
        self._method_wise_path_info.add_api_route(method, path, handler)

    def get(self, route: str) -> None:
        '''
        This defines a new route with get method. Can be used as
        @app.get("/path")
        async def handler():
            ...
        '''
        def wrapper(function: Callable):
            self.add_api_route(Method.GET, route, function)
            return None
        return wrapper

    def post(self, route: str) -> None:
        '''
        This defines a new route with post method. Can be used as
        @app.post("/path")
        async def handler():
            ...
        '''
        def wrapper(function: Callable):
            self.add_api_route(Method.POST, route, function)
            return None
        return wrapper

    def put(self, route: str) -> None:
        '''
        This defines a new route with put method. Can be used as
        @app.put("/path")
        async def handler():
            ...
        '''
        def wrapper(function: Callable):
            self.add_api_route(Method.PUT, route, function)
            return None
        return wrapper

    def patch(self, route: str) -> None:
        '''
        This defines a new route with patch method. Can be used as
        @app.patch("/path")
        async def handler():
            ...
        '''
        def wrapper(function: Callable):
            self.add_api_route(Method.PATCH, route, function)
            return None
        return wrapper

    def delete(self, route: str) -> None:
        '''
        This defines a new route with delete method. Can be used as
        @app.delete("/path")
        async def handler():
            ...
        '''
        def wrapper(function: Callable):
            self.add_api_route(Method.DELETE, route, function)
            return None
        return wrapper
    
    def run(self, host: str="localhost", port: int=8080, debug=False) -> None:
        ServerHandler(self, host, port, debug).start_server()


class RequestHandler:
    _app: Optional[FastPy] = None

    @classmethod
    def set_app(cls, app: FastPy) -> None:
        cls._app = app

    @classmethod
    def get_valid_params_dict(cls, request: Request) -> Dict[str, Any]:
        param_val_dict = {
                **request.path_params.dict(),
                **request.queries.dict(),
                **request.headers.dict()
            }

        kwargs = {}
        for varname, _ in request.annotations.items():
            if varname in param_val_dict:
                kwargs[varname] = param_val_dict[varname]
            else:
                if varname == request.body_param:
                    kwargs[varname] = request.body.value
                elif varname == request.request_param:
                    kwargs[varname] = request
                elif varname == "return":
                    continue
                else:
                    raise HttpException(422, f"{varname} not provided.")
        return kwargs

    @classmethod
    async def handle_request(cls, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            request: Request = await Request.load_from_reader(reader, cls._app._method_wise_path_info)
            kwargs = cls.get_valid_params_dict(request)
            if inspect.isawaitable(request.handler) or inspect.iscoroutinefunction(request.handler) or inspect.iscoroutine(request.handler):
                res = await request.handler(**kwargs)
            else:
                res = request.handler(**kwargs)
            if "return" in request.annotations:
                return_type = request.annotations["return"]
                if return_type is None and res is not None:
                    raise HttpException(
                        500, f"Return type could not be verified. Expected {return_type}, Found {type(res)}")
                elif issubclass(return_type, BaseModel):
                    if isinstance(res, return_type):
                        pass
                    else:
                        try:
                            if isinstance(res, str):
                                res = return_type.model_validate_json(res)
                            else:
                                res = return_type.model_validate(res)
                        except Exception as e:
                            raise HttpException(
                                500, f"Return type could not be verified. Expected {return_type}, Found {type(res)}"
                            )
                else:
                    try:
                        res = return_type(res)
                    except:
                        raise HttpException(
                            500, f"Return type could not be verified. Expected {return_type}, Found {type(res)}"
                        )
            if not isinstance(res, Response):
                res = Response(
                    200,
                    Headers(cookies=None, header_params=[
                            HeaderParam("Content-Type", "Application/Json")]),
                    Body(res)
                )
        except Exception as e:
            res = e
        try:
            await res.write_to_stream(writer)
        except Exception as e:
            print(e)
            traceback.print_exc()
            await Response(500).write_to_stream(writer)

class ServerHandler:
    server = None

    def __init__(
        self,
        app: FastPy,
        host: str, 
        port: int,
        debug: bool
    )-> None:
        ServerHandler.app = app
        ServerHandler.host = host
        ServerHandler.port = port
        ServerHandler.debug = debug

    @classmethod
    async def _start_server(
        cls
    ) -> None:
        RequestHandler.set_app(cls.app)
        server = await asyncio.start_server(RequestHandler.handle_request, cls.host, cls.port)
        addr = server.sockets[0].getsockname()
        print("Server running at", addr)
        async with server:
            await server.serve_forever()

    @classmethod
    def start_server(
        cls
    ) -> None:
        '''
        Starts a web server at given host and port and maps the given app with this port.
        '''
        cls.server = asyncio.create_task(asyncio.run(cls._start_server()))
