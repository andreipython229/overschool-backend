import os
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import declarative_base, DeclarativeBase, sessionmaker

load_dotenv()
meta = MetaData()

# Initialize declarative base with metadata
Base: DeclarativeBase = declarative_base(metadata=meta)

print(os.getenv('POSTGRES_USER'))

engine = create_engine(
    f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_USER_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB_NAME')}",
    echo=True
)


def setup_database() -> None:
    with engine.connect() as conn:
        meta.reflect(bind=engine)


session_maker = sessionmaker(engine, expire_on_commit=False)


def get_session():
    with session_maker() as session:
        yield session

