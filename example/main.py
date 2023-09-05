from src import FastPy, Headers, Cookies, HttpException
from pydantic import BaseModel

class StudentIn(BaseModel):
    name: str
    roll: int

class Student(BaseModel):
    id: int
    name: str
    roll: int

app = FastPy()

CNT_ID = 0
STUDENTS = {}

@app.post("/createStudent")
async def create_student(student: StudentIn) -> Student:
    global CNT_ID
    global STUDENTS
    CNT_ID += 1
    id = CNT_ID
    STUDENTS[id] = student.model_dump()
    STUDENTS[id]["id"] = id
    return STUDENTS[id]

@app.get("/getStudent/{id}")
async def get_student(id: int) -> Student:
    if id in STUDENTS:
        return STUDENTS[id]
    else:
        raise HttpException(404, f"Student not found for id {id}.")
    
@app.get("/verifyHeaders")
async def verify_headers(authentication: str = Headers()) -> str:
    return authentication

@app.get("/verifyCookies")
async def verify_cookies(name: str = Cookies(), roll: str = Cookies()):
    return {"name": name, "roll": roll}