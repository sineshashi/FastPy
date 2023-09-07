from typing import Any, Optional, List, Dict, Set
from pydantic import BaseModel
import json
import datetime


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
        elif not isinstance(self.value, str):
            return json.dumps(self.value)
        return self.value

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
    def __init__(self, cookies: Optional[Cookies] = None, header_params: List[HeaderParam] = []) -> None:
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
        if "cookie" in d:
            del d["cookie"]
        return d
