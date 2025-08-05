from sqlmodel import create_engine, SQLModel , Session
from typing import Generator


DATABASE_URL= 'postgresql://postgres:12345678@localhost:5432/digitalSignage'

engine = create_engine(DATABASE_URL, echo = True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session: 
        yield session 