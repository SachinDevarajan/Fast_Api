from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import jwt
import secrets

from datetime import timedelta, datetime, timezone

from database import engine, Base, get_db
from models import *
from schemas import *

SECURITY_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get('/')
def home():
    return {"message":"This is Our home page"}


students = [
    Student(id=1, name="Sachin",age=24,email='sachin@gmail.com'),
    Student(id=2, name="Keerthi",age=23,email='keerthi@gmail.com'),
    Student(id=3, name="Abhinai",age=23,email='abhinai@gmail.com'),
    Student(id=4, name="Abhinai",age=23,email='abhinai@gmail.com'),

]

@app.get('/viewstudents/')
def viewstudents():
    return students


@app.post('/addstudent/')
def addstudent(student : Student):
    for stud in students:
        if stud.id == student.id:
            raise HTTPException(status_code=400, detail="Student ID Already Present...")

    students.append(student)
    return {"message":"Student Created successfully...", "data":student}



@app.put('/updatestudent/{student_id}')
def updatestudent(student_id: int, updated: Student):
    for index, student in enumerate(students):
        if student.id == student_id:
            if updated.id != student_id:
                raise HTTPException(status_code=400, detail="Student ID cannot be changed..."  )
            students[index] = updated
            return { "message": "Student updated successfully", "data": updated }
        
    raise HTTPException(status_code=404, detail="Student Not Found...." )


@app.delete("/deletestudent/{student_id}")
def delete_student(student_id:int):
    for index, student in enumerate(students):
        if student.id == student_id:
            students.pop(index)
            return {"message": "Student deleted"}

    raise HTTPException( status_code=404, detail="Student not found" )


"""DataBase CRUD operations"""

@app.post("/addstudent", status_code=201)
def add_student( student: Student, db: Session = Depends(get_db)):
    new_student = StudentDB(**student.model_dump())

    db.add(new_student)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException( status_code=409,detail="Student ID or email already exists")

    db.refresh(new_student)

    return {
        "message": "Student added successfully",
        "data": Student.model_validate(new_student)
    }


@app.get("/students")
def get_students(db: Session = Depends(get_db)):

    students = db.scalars(select(StudentDB)).all()

    return students


@app.get("/students/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(StudentDB, student_id)

    if not student:
        raise HTTPException(status_code=404,detail="Student not found" )

    return student


@app.put("/updatestudent/{student_id}")
def update_student( student_id: int, updated: Student,db: Session = Depends(get_db)):
    student = db.get(StudentDB, student_id)

    if not student:
        raise HTTPException( status_code=404,detail="Student not found" )

    if updated.id != student_id:
        raise HTTPException( status_code=400, detail="Student ID cannot be changed" )

    student.name = updated.name
    student.age = updated.age
    student.email = updated.email

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException( status_code=409, detail="Email already exists")

    db.refresh(student)

    return { "message": "Student updated successfully", "data": student}


@app.delete("/deletestudent/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(StudentDB, student_id)
    if not student:
        raise HTTPException( status_code=404, detail="Student not found" )
    db.delete(student)
    db.commit()

    return {"message": "Student deleted successfully"}


''' Login  '''
@app.post('/login/')
def login(data:UserLogin, db:Session=Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == data.email).first()

    if user is None or user.password != data.password:
        raise HTTPException(
            status_code=404,
            detail="The username or Password is wrong...."
        )

    payload = {
        'id' : user.id,
        'email': user.email,
        'exp' : datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    token = jwt.encode(
        payload,
        SECURITY_KEY,
        algorithm=ALGORITHM
    )

    return {
        'message':'Login Successfull....',
        'access_token' : token
    }