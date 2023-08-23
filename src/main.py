import asyncio, enum, json
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

class CookiesParam:
    def __init__(
        self,
        name: str,
        val: Any
    ) -> None:
        self.name = name
        self.value = val
    
    def __str__(self) -> str:
        return f"{self.name}={self.value}"
    
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

class Cookies:
    def __init__(self, cookie_params: List[CookiesParam] = []) -> None:
        self._params = {c.name: c for c in cookie_params}

    def __str__(self) -> str:
        s = ""
        size = len(self._params)
        for i, cookie in enumerate(self._params.values()):
            s += str(cookie)
            if i != size-1:
                s += "; "
        return s

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def from_string(cls, s: str) -> "Cookies":
        cookies = cls()
        for cookie in s.split("; "):
            [k, v] = cookie.split("=")
            cookies._params[k.strip()] = CookiesParam(k.strip(), v.strip())
        return cookies

class Request:
    def __init__(
        self,
        path: str,
        method: Method,
        queries: List[Query],
        headers: List[HeaderParam],
        cookies: Optional[Cookies]=None,
        body: Optional[Body]=None
    ) -> None:
        self.path = path
        self.method = method
        self.queries = {q.name: q for q in queries}
        self.headers = {h.name: h for h in headers}
        self.cookies = cookies
        self.body = body

    @classmethod
    async def load_from_reader(cls, reader: asyncio.StreamReader) -> "Request":
        request_line = await reader.readuntil(b"\r\n")
        method, path, _ = request_line.decode().strip().split(" ")
        headers = []
        queries = []
        cookies = None
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
                continue
            if header_name.casefold().strip() == "content-length":
                content_length = int(header_value.strip())
            if header_name.casefold().strip() == "content-type":
                content_type = header_value.casefold().strip()
            headers.append(HeaderParam(header_name.strip(), header_value.strip()))

        if "?" in path:
            path, query_string = path.split("?", 1)
            query_params = query_string.split("&")
            for param in query_params:
                name, value = param.split("=")
                queries.append(Query(name, value))
        
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
            cookies,
            body
        )

class Response:
    def __init__(
        self,
        status_code: int,
        headers: List[HeaderParam] = [],
        cookies: Optional[Cookies] = None,
        response_body: Optional[Body] = None
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        self.cookies = cookies
        self.reponse_body = response_body

    def __str__(self) -> str:
        s = f"HTTP/1.1 {self.status_code} {HTTP_STATUS_CODES[self.status_code]}\r\n"
        for header in self.headers:
            s += str(header)+"\r\n"
        if self.cookies is not None:
            s += "Set-Cookie: " + str(self.cookies) + "\r\n"
        s += "\r\n"
        s += str(self.reponse_body)
        return s 

async def handle_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    request = await Request.load_from_reader(reader)
    response = Response(
        status_code=200,
        headers = request.headers.values(),
        cookies = request.cookies,
        response_body=request.body
    )
    writer.write(str(response).encode())
    await writer.drain()
    writer.close()

async def main() -> None:
    server = await asyncio.start_server(handle_request, "localhost", 8080)
    addr = server.sockets[0].getsockname()
    print("Server running at", addr)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())