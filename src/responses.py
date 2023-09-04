from typing import Optional
from .params import Headers, Body, Cookies, Cookie
import asyncio
import traceback
from .status_codes import HTTP_STATUS_CODES


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
