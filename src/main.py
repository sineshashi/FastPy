import asyncio

async def handle_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    data = await reader.read(500)
    message = data.decode()
    print("Request Message:", message)

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