import asyncio, enum, json, datetime, traceback
from typing import List, Optional, Type, Union, Any
from pydantic import BaseModel

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

class Method(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

class Query:
    def __init__(
        self,
        name: str,
        val: Any
    ) -> None:
        self.name = name
        self.value = val
    
    def __str__(self) -> str:
        return f"?{self.name}={self.value}"
    
    def __repr__(self) -> str:
        return str(self)

class PathParam:
    def __init__(
        self,
        # name: str,
        val: Any
    ) -> None:
        # self._name = name
        self.value = val

class HeaderParam:
    def __init__(
        self,
        name: str,
        val: str
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
        return json.dumps(self.value)
    
    def __repr__(self) -> str:
        return str(self)
    
class Cookie:
    def __init__(
        self,
        name: str,
        value: str,
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
    
    def add(self, cookie: Cookie) -> None:
        self._params[cookie.name] = cookie

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
    
    def add_query(self, name: str, value: Any) -> None:
        self._queries[name] = {name, Query(name, value)}
    
class PathList:
    def __init__(self, path_params: List[PathParam] = []) -> None:
        self._path_params = path_params

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

class Request:
    def __init__(
        self,
        path: str,
        method: Method,
        queries: QueryList,
        headers: Headers,
        body: Optional[Body]=None
    ) -> None:
        self.path = path
        self.method = method
        self.queries = queries
        self.headers = headers
        self.body = body

    @property
    def cookies(self) -> Cookies:
        return self.headers.cookies

    @classmethod
    async def load_from_reader(cls, reader: asyncio.StreamReader) -> "Request":
        request_line = await reader.readuntil(b"\r\n")
        method, path, _ = request_line.decode().strip().split(" ")
        headers = Headers()
        queries = QueryList()
        cookies = Cookies()
        body = None
        content_length = None
        content_type = None
        while True:
            header_line = await reader.readuntil(b"\r\n")
            header = header_line.decode().strip()
            if not header:
                break

            header_name, header_value = header.split(":", 1)
            if header_name.casefold().strip() == "cookie":
                cookies = Cookies.from_string(header_value)
                headers.set_cookies(cookies)
            if header_name.casefold().strip() == "content-length":
                content_length = int(header_value.strip())
            if header_name.casefold().strip() == "content-type":
                content_type = header_value.casefold().strip()
            headers.add_header(header_name.strip(), header_value.strip())
        
        if "?" in path:
            path, query_string = path.split("?", 1)
            query_params = query_string.split("&")
            for param in query_params:
                name, value = param.split("=")
                queries.add_query(name, value)
        
        if content_length is not None:
            if content_length > 0:
                body_data = await reader.readexactly(content_length)
                if content_type is not None:
                    if "application/json" in content_type:
                        body = json.loads(body_data)
        return cls(
            path,
            method,
            queries,
            headers,
            body
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

async def handle_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        request = await Request.load_from_reader(reader)
        response = Response(
            status_code=200,
            headers = Headers(cookies=None, header_params=[HeaderParam("Content-Type", "Application/Json")]),
            response_body=request.body
        )
        await response.write_to_stream(writer)
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