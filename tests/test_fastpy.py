import sys

sys.path.append('../')


import unittest, asyncio
from src.fastpy_rest.main import FastPy, RequestHandler
from src.fastpy_rest.responses import Response
from src.fastpy_rest.params import Headers, Body, Cookies, PathList, PathParam, QueryList
from src.fastpy_rest.exceptions import HttpException
from src.fastpy_rest.core import Method
from src.fastpy_rest.requests import Request
from src.fastpy_rest.status_codes import HTTP_STATUS_CODES

class TestFastPy(unittest.TestCase):

    def setUp(self):
        self.app = FastPy()

    def test_add_api_route(self):
        @self.app.get("/test")
        async def test_handler():
            return "Test Route"

        self.assertEqual(len(self.app._method_wise_path_info.paths[Method.GET]), 1)

    def test_request_handler_valid_route(self):
        @self.app.get("/test/{param}")
        async def test_handler(param: str):
            return f"Test Route with param: {param}"

        request = Request("/test/123", Method.GET, QueryList(), Headers(), PathList([PathParam("param", "123")]), self.app._method_wise_path_info.get_api_route_path_info(Method.GET, "/test/123"), None)
        kwargs = RequestHandler.get_valid_params_dict(request)
        response = asyncio.run(request.handler(**kwargs))

        self.assertEqual(response, "Test Route with param: 123")

    def test_request_handler_invalid_route(self):
        request = Request("/invalid-route", Method.GET, {}, Headers(), {}, PathList(), None)

        context = self.app._method_wise_path_info.get_api_route_path_info(Method.POST, "/wrong")
        self.assertEqual(context, None)

    def test_response_format(self):
        response = Response(200, Headers(), Body("Hello, World!"))

        expected_response = f"HTTP/1.1 200 {HTTP_STATUS_CODES[200]}\r\n\r\nHello, World!"
        self.assertEqual(str(response), expected_response)

if __name__ == '__main__':
    unittest.main()
