from database import SessionLocal
from models import User

sa = SessionLocal()
manager = User(username="admin", password="admin123", role="manager")
sa.add(manager)
    
sa.commit()

s = SessionLocal()
staff = User(username="staff1", password="1234", role="staff")
s.add(staff)

s.commit()


print("Staff account created.")
