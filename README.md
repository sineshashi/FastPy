# FastPy - A Simple Python Web Framework

FastPy is a lightweight Python web framework designed for educational purposes. It provides a simple and easy-to-understand structure to help you learn the fundamentals of building a web framework from scratch. With FastPy, you can explore various aspects of web development, including routing, request handling, response generation, and more.

## Features

* Minimalistic design for educational purposes.
* Supports common HTTP methods (GET, POST, PUT, PATCH, DELETE).
* Route handling and request processing.
* Exception handling for HTTP errors.
* Asynchronous request handling with asyncio.
* Basic support for request parameters, headers, and cookies.

## Getting Started

To get started with FastPy, follow these steps:

1. Clone the FastPy repository
2. Install the required dependencies: `pip install -r requirements.txt`
3. Create your own routes and handlers
4. Start the server

   ```python
   from src import FastPy

   app = FastPy()

   @app.get("/get")
   async def get(id: int):
      return id

   if __name__ == "__main__":
      app.run()
   ```

## Documentation

### Defining Routes

This project is highly inspired by FastAPI and it has the very same route defining syntax too, using decorators. The handler function may or may not be async, framework takes care of that by itself whether to await or call without await.

```python
@app.get("/path")
async def get_handler():
   ...

```

Similary other methods like `post`, `put`, `patch` and `delete` can be defined.

### Various Input Parameters

#### Query Params

We can take query params in our handlers by simply taking input parameters with type annotations except some annotations which we will discuss in body, headers, cookies and path.

```python
@app.get("/path")
async def get_handler(id: int):
   return id
```

#### Path Params

Any parameter in handler function which is mentioned in path as `/{path_param}` will be considered a path parameter.

```python
@app.get("/path/{id}")
async def get_handler(id: int):
   return id
```

#### Body

Any parameter with annotation of subclass of `BaseModel` defined in `pydantic` is considered as a body json and body will be validated according to this body.

```python
from pydantic import BaseModel

class StudentIn(BaseModel):
   name: str
   class: int

@app.post("/create")
async def create_student(student: StudentIn):
    return student
```

#### Headers

Parameters with primitive type annotations along with default value of `Headers` will be extracted from headers.

```python
from src import Headers

@app.get("/path")
async def handler(authorization: str = Headers())):
   return {"authorization": authorization}
```

#### Cookies

Very same as headers, instead of `Headers()`, `Cookies` is used as a default value.

### Data Serialization and Validation

For the purpose of serialization, deserialization and validation, Pydantic is used heavily. For body, we can denote it in a pydantic model and deserialize accordingly. In the framework, input annotations are mandatory and data is deserialized according to those annotations. Return annotation is not mandatory but we can also define that and enforce the validation of output data.

```python
from pydantic import BaseModel

class StudentIn(BaseModel):
   name: str
   class: int

@app.post("/create")
async def create_student(student: StudentIn) -> StudentIn:
    return student
```

### Request Class

To avoid the data validation, `Request` class can be used in annotations and in handler, request object will be provider with parsed path, query and other params.

```python
from src import Request

@app.post("/create")
async def create_student(request: Request):
    ...
```

### Response Class

To send custom status code for success (default=200), Response class object should be returned from handler. In this case, return type will not be validated.

```python
from src import Request, Response

@app.post("/create")
async def create_student(request: Request):
    return Response(201, "Student has been created.")
```

### Custom Exceptions

To raise exceptions with appropriate code and messages, `HttpException` class has been defined.

```python
from src import Request, HttpException

@app.post("/create")
async def create_student(request: Request):
    raise HttpException(401, "Request not authenticated.")
```

## Testing

You can run the provided unit tests to verify the functionality of FastPy. To run all the tests, use the following command:

```bash
python -m unittest discover -p 'test_*.py'
```

## Contributing

FastPy is intended for educational purposes and may not be suitable for production use. If you'd like to contribute to the project or have any suggestions, please feel free to create an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE]([https://github.com/sineshashi/FastPy/LICENSE](https://github.com/sineshashi/FastPy/blob/master/LICENSE)) file for details.

## Acknowledgments

FastPy was created as an educational project to help individuals learn the basics of web framework development. We acknowledge the contributions of the open-source community and various educational resources that inspired this project.

---

Happy learning and building with FastPy! 😊
