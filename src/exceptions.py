from typing import Optional
import asyncio
import traceback
import json
from .status_codes import HTTP_STATUS_CODES


class HttpException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: Optional[str] = None
    ) -> None:
        '''
        This sends status_code and detail to the client.
        '''
        if status_code not in HTTP_STATUS_CODES:
            raise HttpException(500, "Wrong http code defined.")
        self.status_code = status_code
        self.detail = json.dumps({"detail": detail})

    def __str__(self) -> str:
        s = f"HTTP/1.1 {self.status_code} {HTTP_STATUS_CODES[self.status_code]}\r\n"
        if self.detail is not None:
            s += "\r\n"
            s += str(self.detail)
        return s

    async def write_to_stream(self, writer: asyncio.StreamWriter) -> None:
        '''
        This writes to stream.
        '''
        try:
            writer.write(str(self).encode())
        except Exception as e:
            print(e)
            traceback.print_exc()
            writer.write("HTTP/1.1 500 Internal Server\r\n".encode())
        finally:
            await writer.drain()
            writer.close()
