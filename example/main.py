from src import FastPy, Headers, Cookies

app = FastPy()

@app.get("/get/{id}")
async def get_id(name: str, id: int) -> int:
    print(name, id, "get called.")
    return id