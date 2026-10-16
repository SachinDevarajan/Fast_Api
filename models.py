from pydantic import BaseModel, Field

from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, Mapped
from database import Base

class Student(BaseModel):
    id: int
    name: str
    age: int = Field(gt=0)
    email: str


class StudentDB(Base):
    __tablename__ = 'students'
    id : Mapped[int] = mapped_column(Integer,primary_key=True)
    name : Mapped[str] = mapped_column(String(100))
    age : Mapped[int] = mapped_column(Integer)
    email : Mapped[str] = mapped_column(String(150),unique=True)


class UserDB(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(Integer,primary_key=True, index=True)
    username : Mapped[str] = mapped_column(String, nullable=False)
    email : Mapped[str] = mapped_column(String, nullable=False)
    password : Mapped[str] = mapped_column(String, nullable=False)
    role :Mapped[str] = mapped_column(String,default='student',nullable=False)
