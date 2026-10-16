from database import SessionLocal
from models import UserDB

db = SessionLocal()

try:
    email = "sachin@gmail.com"

    user = db.query(UserDB).filter(UserDB.email == email).first()

    if user is None:
        print("User not found. Register first.")
    else:
        user.role = "admin"
        db.commit()
        print("Admin role assigned successfully.")

finally:
    db.close()