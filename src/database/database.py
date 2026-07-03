from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL

# Registrar os models
# import models.athlete
# import models.evaluation


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
)


def create_database():

    Base.metadata.create_all(bind=engine)