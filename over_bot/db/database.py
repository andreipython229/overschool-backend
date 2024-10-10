import os

from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, declarative_base, sessionmaker

load_dotenv()
meta = MetaData()

# Initialize declarative base with metadata
Base: DeclarativeBase = declarative_base(metadata=meta)

print(os.getenv("POSTGRES_USER"))

try:
    engine = create_engine(
        f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_USER_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB_NAME')}",
        echo=True,
    )
except SQLAlchemyError as e:
    print(f"Ошибка при создании подключения к базе данных: {e}")
    raise


def setup_database() -> None:
    try:
        with engine.connect() as conn:
            meta.reflect(bind=engine)
    except SQLAlchemyError as e:
        print(f"Ошибка при настройке базы данных: {e}")
        raise


session_maker = sessionmaker(engine, expire_on_commit=False)


def get_session():
    try:
        with session_maker() as session:
            yield session
    except SQLAlchemyError as e:
        print(f"Ошибка при получении сессии: {e}")
        raise
