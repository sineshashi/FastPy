import asyncio, enum, json, datetime, traceback, inspect, re
from typing import List, Optional, Type, Union, Any, Dict, Tuple, Callable, Set
from pydantic import BaseModel
from collections import defaultdict

HTTP_STATUS_CODES = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",

    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",

    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    307: "Temporary Redirect",
    308: "Permanent Redirect",

    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",

    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required"
}

class Method(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

class Query:
    def __init__(
        self,
        name: str,
        val: Any,
        is_pre_defined: bool
    ) -> None:
        self.name = name
        self.value = val
        self.pre_defined = is_pre_defined
    
    def __str__(self) -> str:
        return f"?{self.name}={self.value}"
    
    def __repr__(self) -> str:
        return str(self)

class PathParam:
    def __init__(
        self,
        name: str,
        val: Any
    ) -> None:
        self.name = name
        self.value = val

class HeaderParam:
    def __init__(
        self,
        name: str,
        val: Any
    ) -> None:
        self.name = name
        self.value = val
    
    def __str__(self) -> str:
        return f"{self.name}: {self.value}"
    
    def __repr__(self) -> str:
        return str(self)

class Body:
    def __init__(
        self,
        value: Any
    ) -> None:
        self.value = value

    def __str__(self) -> str:
        if isinstance(self.value, BaseModel):
            return self.value.model_dump_json()
        return json.dumps(self.value)
    
    def __repr__(self) -> str:
        return str(self)
    
class Cookie:
    def __init__(
        self,
        name: str,
        value: Any,
        expires: Optional[datetime.datetime] = None,
        max_age: Optional[int] = None,
        domain: Optional[str] = None,
        path: Optional[str] = None,
        same_site: Optional[str] = None,
        priority: Optional[str] = None,
        secure: bool = False,
        http_only: bool = False
    ) -> None:
        self.name = name
        self.value = value
        self.expires = expires
        self.max_age = max_age
        self.domain = domain
        self.path = path
        self.same_site = same_site
        self.priority = priority
        self.secure = secure
        self.http_only = http_only

    def __str__(self) -> str:
        s = ""
        s += f"{self.name}={self.value}"
        if self.expires is not None:
            s += f"; Expires={self.expires.isoformat()}"
        if self.max_age is not None:
            s += f"; Max-Age={self.max_age}"
        if self.domain is not None:
            s += f"; Domain={self.domain}"
        if self.path is not None:
            s += f"; Path={self.path}"
        if self.same_site is not None:
            s += f"; SameSite={self.same_site}"
        if self.priority is not None:
            s += f"; Priority={self.priority}"
        if self.secure:
            s += f"; Secure"
        if self.http_only:
            s += f"; HttpOnly"
        return s

class Cookies:
    def __init__(self, cookie_params: List[Cookie] = []) -> None:
        self._params = {c.name: c for c in cookie_params}

    def __str__(self) -> str:
        s = ""
        for cookie in self._params.values():
            s += f"Set-Cookie: {str(cookie)}"
            s += "\r\n"
        return s

    def __repr__(self) -> str:
        return str(self)
    
    def __contains__(self, c: str) -> bool:
        return c in self._params
    
    def get(self, c: str) -> Cookie:
        return self._params[c]
    
    @property
    def cookie_names(self) -> Set[str]:
        return set(self._params.keys())
    
    def add(self, cookie: Cookie) -> None:
        self._params[cookie.name] = cookie

    def update_cookie(self, name: str, value: Any) -> None:
        self._params[name] = Cookie(name, value)

    def dict(self) -> Dict[str, Any]:
        return {c.name: c.value for c in self._params.values()}

    @classmethod
    def from_string(cls, s: str) -> "Cookies":
        cookies = cls()
        for cookie in s.split("; "):
            [k, v] = cookie.split("=")
            cookies._params[k.strip()] = Cookie(k.strip(), v.strip())
        return cookies
    
class QueryList:
    def __init__(self, queries: List[Query] = []) -> None:
        self._queries = {q.name: q for q in queries}

    @property
    def queries(self) -> List[Query]:
        return self._queries.values()
    
    def add_query(self, name: str, value: Any, pre_defined: bool) -> None:
        self._queries[name] = Query(name, value, pre_defined)

    def dict(self) -> None:
        return {q.name: q.value for q in self._queries.values()}
    
class PathList:
    def __init__(self, path_params: List[PathParam] = []) -> None:
        self._path_params = {p.name: p for p in path_params}

    def add_path(self, name: str, value: Any) -> None:
        self._path_params[name] = PathParam(name, value)

    def dict(self) -> Dict[str, Any]:
        return {p.name: p.value for p in self._path_params.values()}

class Headers:
    def __init__(self, cookies: Optional[Cookies]=None, header_params: List[HeaderParam] = []) -> None:
        self.cookies = cookies if cookies is not None else Cookies()
        self.header_params = {h.name: h for h in header_params}

    def __str__(self) -> str:
        s = ""
        for h in self.header_params.values():
            s += f"{h.name}: {h.value}\r\n"
        s += str(self.cookies)
        return s
    
    def add_header(self, name: str, value: str) -> None:
        self.header_params[name] = HeaderParam(name, value)

    def add_cookie(self, cookie=Cookie) -> None:
        self.cookies.add(cookie)

    def set_cookies(self, cookies=Cookies) -> None:
        self.cookies = cookies

    def dict(self) -> Dict[str, Any]:
        d = self.cookies.dict()
        for h in self.header_params.values():
            d[h.name] = h.value
        return d

class PathInfo:
    def __init__(
        self, 
        route: str,
        handler: Callable,
        path_params: Tuple[str] = Tuple(),
        query_params: Set[str] = set(),
        headers: Set[str] = set(),
        cookies: Set[str] = set(),
        defaults: Dict[str, Any] = {},
        var_types: Dict[str, Callable] = {},
        body: Optional[str] = None,
        response_model: Optional[BaseModel] = None,
        request_param: Optional[str] = None
    ) -> None:
        self.route = route
        self.path_params = path_params
        self.query_params = query_params
        self.headers = headers
        self.cookies = cookies
        self.defaults = defaults
        self.var_types = var_types
        self.handler = handler
        self.body = body
        self.response_model = response_model
        self.request_param = request_param

    def verify_path_params(self, *args) -> PathList:
        path = PathList()
        for p, pval in zip(self.path_params, args):
            try:
                path.add_path(p, self.var_types[p](pval))
            except:
                raise Exception("Change to better exception.")
        return path

    def verify_query_params(self, **kwargs) -> QueryList:
        query_list = QueryList()
        for q in self.query_params:
            if q not in kwargs and q in self.defaults:
                raise Exception("Change to better exception.")
            var_type = self.var_types[q]
            if q in kwargs:
                q_val = kwargs.get(q)
            else:
                q_val = self.defaults[q]
            try:
                q_val = var_type(q_val)
                query_list.add_query(q, q_val, True)
            except:
                raise Exception("Change to better exception.")
        for extra_q in set(kwargs.keys()).difference(self.query_params):
            query_list.add_query(extra_q, kwargs[extra_q], False)
        return query_list
    
    def verify_cookies(self, cookies_str: str) -> Cookies:
        cookies = Cookies.from_string(cookies_str)
        for c in self.cookies:
            if c not in cookies and c not in self.defaults:
                raise Exception("Change to better exception.")
            var_type = self.var_types[c]
            if c in cookies:
                c_val = cookies.get(c).value
            else:
                c_val = self.defaults[c]
            try:
                cookies.update_cookie(name=c, value=var_type(c_val))
            except:
                raise Exception("Change to better exception.")
        return cookies
    
    def verify_headers(self, **kwargs) -> Headers:
        headers = Headers()
        for h in self.headers:
            if h not in kwargs and h not in self.defaults:
                raise Exception("Change to better exception.")
            var_type = self.var_types[h]
            if h in kwargs:
                h_val = kwargs[h]
            else:
                h_val = self.defaults[h]
            try:
                h_val = var_type(h_val)
                headers.add_header(h, h_val)
            except:
                raise Exception("Change to better exception.")
        for extra_h in set(kwargs.keys()).difference(self.headers):
            if extra_h.casefold() == "cookie":
                cookies = self.verify_cookies(kwargs[extra_h])
                headers.set_cookies(cookies)
            else:
                headers.add_header(extra_h, kwargs[extra_h])
        return headers
    
    def verify_body(self, value: Any) -> Body:
        if self.body is not None:
            var_type = self.var_types[self.body]
            try:
                return Body(var_type.parse_obj(value))
            except:
                raise Exception("Change to better exception.")
        else:
            return Body(value)

class RegisteredPaths:
    def __init__(self) -> None:
        self.paths: Dict[str, List[PathInfo]] = defaultdict(list)

    def _get_path_params(self, route: str) -> Tuple[str, Tuple[str]]:
        pattern = r'\{([^{}]+)\}'
        parts = re.split(pattern, route, 1)
        variable_names = re.findall(pattern, route)
        return parts[0], variable_names

    def add_api_route(self, route: str, function: Callable) -> None:
        original_route, params = self._get_path_params(route)
        params = set(params)
        function_details = inspect.getfullargspec(function)
        annotations = function_details.annotations
        args = function_details.args
        defaults = function_details.defaults
        defaults_dict = {}
        queries = set()
        headers = set()
        cookies = set()
        body = None
        request = None
        for arg, default in zip(args[-len(defaults):], defaults):
            defaults_dict[arg] = default
        for varname, _ in annotations.items():
            default = defaults_dict[varname]
            if isinstance(default, Headers):
                headers.add(varname)
            elif isinstance(default, Cookies):
                cookies.add(varname)
            elif default in params or "return" == varname:
                continue
            elif isinstance(default, BaseModel):
                body = varname
            elif annotations[varname] == Request:
                request = varname
            else:
                queries.add(varname)
        response_model = None
        if "return" in annotations:
            response_model = annotations["return"]
        self.paths[original_route].append(PathInfo(
            route=route,
            handler=function,
            path_params=params,
            query_params=queries,
            headers=headers,
            cookies=cookies,
            defaults=defaults_dict,
            var_types=annotations,
            body=body,
            response_model=response_model,
            request_param=request
        ))

    def get_api_path_info(self, route: str) -> Optional[PathInfo]:
        if route.endswith("/"):
            route = route[:-1]
        parts = route.split("/")
        i = len(parts) - 1
        while i >= 0:
            cnt_path = parts[:i+1].join("/")
            for pathinfo in self.paths[cnt_path]:
                pattern = r'\{([^{}]+)\}'
                match = re.match(pathinfo.route, route)
                if match:
                    variable_values = match.groups()
                    variable_names = re.findall(pattern, pathinfo.route)
                    for var, var_val in zip(variable_names, variable_values):
                        if var in pathinfo.path_params:
                            try:
                                pathinfo.var_types[var](var_val)
                            except:
                                ...
                    return pathinfo
            i -= 1 
        return None

class MethodWisePathsInfo:
    def __init__(self) -> None:
        self.paths: Dict[Method, RegisteredPaths] = {
            method: RegisteredPaths() for method in Method._member_names_
        }
    
    def add_api_route(self, method: Method, route: str, function: Callable) -> None:
        self.paths[method].add_api_route(route, function)

    def get_api_route_path_info(self, method: Method, route: str) -> Optional[PathInfo]:
        if "?" in route:
            idx = route.find("?")
            return route[:idx]
        return self.paths[method].get_api_path_info(route)
    
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
            #@TODO raise exception.
            ...

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
    
class Response:
    def __init__(
        self,
        status_code: int,
        headers: Optional[Headers] = None,
        response_body: Optional[Body] = None
    ) -> None:
        self.status_code = status_code
        self.headers = headers if headers is not None else Headers()
        self.reponse_body = response_body

    @property
    def cookies(self) -> Cookies:
        return self.headers.cookies
    
    def add_cookie(self, cookie: Cookie) -> None:
        self.headers.add_cookie(cookie)
    
    def set_cookies(self, cookies: Cookies) -> None:
        self.headers.set_cookies(cookies)

    async def write_to_stream(self, writer: asyncio.StreamWriter) -> None:
        try:
            print(str(self))
            writer.write(str(self).encode())
        except Exception as e:
            print(e)
            traceback.print_exc()
            writer.write("HTTP/1.1 500 Internal Server\r\n".encode())
        finally:
            await writer.drain()
            writer.close()

    def __str__(self) -> str:
        s = f"HTTP/1.1 {self.status_code} {HTTP_STATUS_CODES[self.status_code]}\r\n"
        s += str(self.headers)
        s += "\r\n"
        s += str(self.reponse_body)
        return s 

class FastPy:
    def __init__(self) -> None:
        self._method_wise_path_info = MethodWisePathsInfo()

    def add_api_route(self, method: Method, path: str, handler: Callable) -> None:
        self._method_wise_path_info.add_api_route(method, path, handler)

    def get(self, route: str, function: Callable) -> None:
        self.add_api_route(Method.GET, route, function)
    
    def post(self, route: str, function: Callable) -> None:
        self.add_api_route(Method.POST, route, function)

    def put(self, route: str, function: Callable) -> None:
        self.add_api_route(Method.PUT, route, function)

    def patch(self, route: str, function: Callable) -> None:
        self.add_api_route(Method.PATCH, route, function)

    def delete(self, route: str, function: Callable) -> None:
        self.add_api_route(Method.DELETE, route, function)


async def handle_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        request: Request = await Request.load_from_reader(reader)
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
                    raise Exception("A better exception.")
        try:
            if inspect.isawaitable(request.handler):
                res = await request.handler(**kwargs)
            else:
                res = request.handler(**kwargs)
            if "return" in request.annotations:
                return_type = request.annotations["return"]
                if return_type is None and res is not None:
                    raise Exception()
                elif issubclass(return_type, BaseModel):
                    if isinstance(res, return_type):
                        pass
                    else:
                        try:
                            res = return_type(res)
                        except:
                            raise Exception()
                else:
                    try:
                        res = return_type(res)
                    except:
                        raise Exception()
            if not isinstance(res, Response):
                res = Response(
                    200, 
                    Headers(cookies=None, header_params=[HeaderParam("Content-Type", "Application/Json")]), 
                    Body(res)
                )
        except:
            res = Exception() #Write better exception handler
        await res.write_to_stream(writer)
    except Exception as e:
        print(e)
        traceback.print_exc()
        await Response(500).write_to_stream(writer)

async def main() -> None:
    server = await asyncio.start_server(handle_request, "localhost", 8080)
    addr = server.sockets[0].getsockname()
    print("Server running at", addr)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())