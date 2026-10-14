from pydantic import BaseModel, ConfigDict, Field

class Student(BaseModel):
    id: int
    name: str
    age: int = Field(gt=0)
    email: str
    
    model_config = ConfigDict(from_attributes=True)