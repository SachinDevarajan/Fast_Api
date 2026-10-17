from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

import jwt
from jwt.exceptions import InvalidTokenError

import secrets
from pwdlib import PasswordHash

from datetime import timedelta, datetime, timezone

from database import engine, Base, get_db
from models import *
from schemas import *

import os
from dotenv import load_dotenv

load_dotenv()

SECURITY_KEY = os.environ['SECURITY_KEY']
# print(SECURITY_KEY)
ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()

app = FastAPI()
security = HTTPBearer()

Base.metadata.create_all(bind=engine)


def get_current_user(creadentials:HTTPAuthorizationCredentials=Depends(security),
                     db: Session = Depends(get_db)):
    token = creadentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECURITY_KEY,
            algorithms=[ALGORITHM]
        )
        user_id = int(payload['sub'])

    except (InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or Experid Token"
        )

    user = db.get(UserDB, user_id)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User Not Found"
        )
    
    return user


def admin_required(user: UserDB = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return user



@app.get('/')
def home():
    return {"message":"This is Our home page"}


students = [
    Student(id=1, name="Sachin",age=24,email='sachin@gmail.com'),
    Student(id=2, name="Keerthi",age=23,email='keerthi@gmail.com'),
    Student(id=3, name="Abhinai",age=23,email='abhinai@gmail.com')
]

"""Pydantic CRUD operations"""
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

@app.post("/add_student", status_code=201)
def add_student( student: Student, db: Session = Depends(get_db),
                admin: UserDB = Depends(admin_required)):
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
def get_students(db: Session = Depends(get_db),
                 current_user : UserDB=Depends(get_current_user)):

    students = db.scalars(select(StudentDB)).all()

    return students


@app.get("/students/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db),
                current_user: UserDB = Depends(get_current_user)):
    student = db.get(StudentDB, student_id)

    if not student:
        raise HTTPException(status_code=404,detail="Student not found" )

    return student


@app.put("/updatestudent/{student_id}")
def update_student( student_id: int, updated: Student,db: Session = Depends(get_db),
                   admin: UserDB = Depends(admin_required)):
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
def delete_student(student_id: int, db: Session = Depends(get_db),
                   admin: UserDB = Depends(admin_required)):
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

    if user is None or not password_hash.verify(data.password,user.password):
        raise HTTPException(
            status_code=401,
            detail="The username or Password is wrong...."
        )

    payload = {
        'sub' : str(user.id),
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


@app.post('/register/')
def register(data:UserCreate , db:Session=Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == data.email).first()

    if user:
        raise HTTPException(
            status_code=409,
            detail="Email Already Registered"
        )
    hashed = password_hash.hash(data.password)

    new_user = UserDB(
        username = data.username,
        email = data.email,
        password = hashed
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        'message':'Registration Successful....',
        'id':new_user.id,
        'username':new_user.username,
        'email':new_user.email
    }


