from pydantic import BaseModel, ConfigDict, Field, EmailStr

class Student(BaseModel):
    id: int
    name: str
    age: int = Field(gt=0)
    email: str
    
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username : str
    email : EmailStr
    password : str


class UserLogin(BaseModel):
    email : EmailStr
    password : str

class UserCreate(BaseModel):
    id : int
    username : str
    email : EmailStr

    model_config = ConfigDict(from_attributes=True)