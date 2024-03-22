from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import create_engine
from sqlalchemy.orm import registry, Session
from fastapi import Depends, HTTPException

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True, future=True)
session = Session(engine)
registry().metadata.create_all(engine)

# declarative base class
Base = declarative_base()

# an example mapping using the base
class User(Base):
    __tablename__ = "user"
   
    id = Column(Integer, primary_key=True)
    name = Column(String)
    boolean = Column(Boolean, default=False)
   



from fastapi import FastAPI

app = FastAPI()



@app.get("/")
async def get_all_todos():
    user_query = session.query(User)
    return user_query.all()





