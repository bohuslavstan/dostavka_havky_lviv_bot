from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.base import Base
from models.users import User, Role, ClientSavedLocation


if __name__ == "__main__":
    engine = create_engine("sqlite:///sample.db", echo=True)

    Base.metadata.create_all(bind=engine)

    session = Session(bind=engine)

    role1 = Role(description="client")

    session.add_all([role1])
    session.commit()