import json
import asyncio
from typing import Set, Dict, Callable, Optional
from .core import Method, PathInfo, MethodWisePathsInfo
from .params import QueryList, Headers, PathList, Body, Cookies
from .exceptions import HttpException


class Request:
    def __init__(
        self,
        path: str,
        method: Method,
        queries: QueryList,
        headers: Headers,
        path_params: PathList,
        path_info: PathInfo,
        body: Body
    ) -> None:
        self.path = path
        self.method = method
        self.queries = queries
        self.headers = headers
        self.body = body
        self.path_params = path_params
        self._path_info = path_info

    @property
    def params(self) -> Set[str]:
        return self._path_info.var_types.keys()

    @property
    def annotations(self) -> Dict[str, Callable]:
        return self._path_info.var_types

    @property
    def handler(self) -> Callable:
        return self._path_info.handler

    @property
    def cookies(self) -> Cookies:
        return self.headers.cookies

    @property
    def request_param(self) -> Optional[str]:
        return self._path_info.request_param

    @property
    def body_param(self) -> Optional[str]:
        return self._path_info.body

    @classmethod
    async def load_from_reader(cls, reader: asyncio.StreamReader, all_path_info: MethodWisePathsInfo) -> "Request":
        request_line = await reader.readuntil(b"\r\n")
        method, path, _ = request_line.decode().strip().split(" ")
        headers = {}
        queries = {}
        body = None
        content_length = None
        content_type = None
        path_info = all_path_info.get_api_route_path_info(method, path)
        if path_info is None:
            raise HttpException(404, "No such route found.")

        if "?" in path:
            path, query_string = path.split("?", 1)
            query_params = query_string.split("&")
            for param in query_params:
                name, value = param.split("=")
                queries[name] = value

        while True:
            header_line = await reader.readuntil(b"\r\n")
            header = header_line.decode().strip()
            if not header:
                break

            header_name, header_value = header.split(":", 1)
            if header_name.casefold().strip() == "content-length":
                content_length = int(header_value.strip())
            if header_name.casefold().strip() == "content-type":
                content_type = header_value.casefold().strip()
            headers[header_name.strip()] = header_value.strip()

        if content_length is not None:
            if content_length > 0:
                body_data = await reader.readexactly(content_length)
                if content_type is not None:
                    if "application/json" in content_type:
                        body = json.loads(body_data)

        number_of_path_params = len(path_info.path_params)
        splits = path.split("/")
        path_vals = splits[-number_of_path_params:]
        route = "/".join(splits[:-number_of_path_params])

        verified_path_params = path_info.verify_path_params(*path_vals)
        verified_query_params = path_info.verify_query_params(**queries)
        verified_headers = path_info.verify_headers(**headers)
        verified_body = path_info.verify_body(body)
        return cls(
            route,
            method,
            verified_query_params,
            verified_headers,
            verified_path_params,
            path_info,
            verified_body
        )
