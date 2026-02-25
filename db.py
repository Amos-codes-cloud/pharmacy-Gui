from connector import engine, Base
import models

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

print("Database reset successfully.")
