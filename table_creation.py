from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models.base import Base, User

if __name__ == "__main__":
    engine = create_engine("sqlite:///sample.db", echo=True)

    Base.metadata.create_all(bind=engine)

    session = Session(bind=engine)

    session.commit()
