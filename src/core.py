import enum
import inspect
import re
from typing import Callable, Tuple, Set, Dict, Optional, Any, List
from pydantic import BaseModel
from .params import PathList, QueryList, Headers, Cookies, Body
from .exceptions import HttpException


class Method(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class PathInfo:
    def __init__(
        self,
        route: str,
        handler: Callable,
        path_params: Tuple[str] = tuple(),
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
                raise HttpException(
                    422, f"{p}, Expected type {self.var_types[p]}, Found {type(pval)}. Value {pval}")
        return path

    def verify_query_params(self, **kwargs) -> QueryList:
        query_list = QueryList()
        for q in self.query_params:
            if q not in kwargs and q in self.defaults:
                raise HttpException(422, f"{q} not given in query params.")
            var_type = self.var_types[q]
            if q in kwargs:
                q_val = kwargs.get(q)
            else:
                q_val = self.defaults[q]
            try:
                q_val = var_type(q_val)
                query_list.add_query(q, q_val, True)
            except:
                raise HttpException(
                    422, f"{q}, Expected type {self.var_types[q]}, Found {type(q_val)}. Value {q_val}")
        for extra_q in set(kwargs.keys()).difference(self.query_params):
            query_list.add_query(extra_q, kwargs[extra_q], False)
        return query_list

    def verify_cookies(self, cookies_str: str) -> Cookies:
        cookies = Cookies.from_string(cookies_str)
        for c in self.cookies:
            if c not in cookies and c not in self.defaults:
                raise HttpException(422, f"{c} not given in cookies.")
            var_type = self.var_types[c]
            if c in cookies:
                c_val = cookies.get(c).value
            else:
                c_val = self.defaults[c]
            try:
                cookies.update_cookie(name=c, value=var_type(c_val))
            except:
                raise HttpException(
                    422, f"{c}, Expected type {self.var_types[c]}, Found {type(c_val)}. Value {c_val}")
        return cookies

    def verify_headers(self, **kwargs) -> Headers:
        headers = Headers()
        for h in self.headers:
            if h not in kwargs and h not in self.defaults:
                raise HttpException(422, f"{h} not given in headers.")
            var_type = self.var_types[h]
            if h in kwargs:
                h_val = kwargs[h]
            else:
                h_val = self.defaults[h]
            try:
                h_val = var_type(h_val)
                headers.add_header(h, h_val)
            except:
                raise HttpException(
                    422, f"{h}, Expected type {self.var_types[h]}, Found {type(h_val)}. Value {h_val}")
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
                return Body(var_type.model_validate_json(value))
            except Exception as e:
                print(e)
                raise HttpException(422, str(e))
        else:
            return Body(value)


class RegisteredPaths:
    def __init__(self) -> None:
        self.paths: Dict[str, List[PathInfo]] = {}

    def _get_path_params(self, route: str) -> Tuple[str, Tuple[str]]:
        pattern = r'\{([^{}]+)\}'
        parts = re.split(pattern, route, 1)
        variable_names = re.findall(pattern, route)
        return parts[0], variable_names

    def add_api_route(self, route: str, function: Callable) -> None:
        from .requests import Request
        original_route, params = self._get_path_params(route)
        params = set(params)
        function_details = inspect.getfullargspec(function)
        annotations = function_details.annotations
        args = function_details.args
        defaults = function_details.defaults
        defaults = [] if defaults is None else defaults
        defaults_dict = {}
        queries = set()
        headers = set()
        cookies = set()
        body = None
        request = None
        for arg, default in zip(args[-len(defaults):], defaults):
            defaults_dict[arg] = default
        for varname, _ in annotations.items():
            default = defaults_dict.get(varname)
            if isinstance(default, Headers):
                headers.add(varname)
            elif isinstance(default, Cookies):
                cookies.add(varname)
            elif varname in params or "return" == varname:
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
        if original_route.endswith("/"):
            original_route = original_route[:-1]
        path_info = PathInfo(
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
        )
        if original_route in self.paths:
            self.paths[original_route].append(path_info)
        else:
            self.paths[original_route] = [path_info]

    def get_api_path_info(self, route: str) -> Optional[PathInfo]:
        if route.endswith("/"):
            route = route[:-1]
        parts = route.split("/")
        i = len(parts) - 1
        while i >= 0:
            cnt_path = "/".join(parts[:i+1])
            if cnt_path not in self.paths:
                i -= 1
                continue
            for pathinfo in self.paths[cnt_path]:
                if len(parts) - i - 1 != len(pathinfo.path_params):
                    continue
                for var, var_val in zip(pathinfo.path_params, parts[i+1:]):
                    if var in pathinfo.path_params:
                        try:
                            pathinfo.var_types[var](var_val)
                        except:
                            raise HttpException(404, "No route found.")
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
            route = route[:idx]
        return self.paths[method].get_api_path_info(route)
