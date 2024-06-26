import os
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, Table, Column, Integer, String, inspect
from sqlalchemy.orm import sessionmaker
from loguru import logger

load_dotenv()

engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_USER_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB_NAME')}",
    echo=True
)

Session = sessionmaker(bind=engine)
session = Session()

meta = MetaData()
meta.bind = engine

school_table = Table('schools_school', meta, autoload_with=engine)
newsletterTemplate_table = Table('schools_newslettertemplate', meta, autoload_with=engine)
sentNewsletter_table = Table('schools_sentnewsletter', meta, autoload_with=engine)
users_table = Table('users_user', meta, autoload_with=engine)
