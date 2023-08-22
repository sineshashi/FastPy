import asyncio, enum, json
from typing import List, Optional, Type, Union, Any
from pydantic import BaseModel

class StatusCode(enum.Enum):
    ...

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
            cookies._params[k] = CookiesParam(k, v)
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
        self._path = path
        self._method = method
        self._queries = {q.name: q for q in queries}
        self._headers = {h.name: h for h in headers}
        self._cookies = cookies
        self._body = body

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
    ...

async def handle_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    request = await Request.load_from_reader(reader)

    addr = writer.get_extra_info("peername")
    print("Writer Address:", addr)

    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json\r\n"
        "\r\n"
        '{"message": "Hello, world!"}'
    )
    writer.write(response.encode())
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