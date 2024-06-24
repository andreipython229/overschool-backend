import os
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, Table, Column, Integer, String, inspect
from sqlalchemy.orm import sessionmaker
from loguru import logger

load_dotenv()

# Подключаемся к базе данных PostgreSQL
engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_USER_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB_NAME')}",
    echo=True
)

# Создаем сессию для взаимодействия с базой данных
Session = sessionmaker(bind=engine)
session = Session()

# Создаем объект MetaData для работы с таблицами
meta = MetaData()
meta.bind = engine

# Получаем список всех таблиц
inspector = inspect(engine)
tables = inspector.get_table_names()
logger.info(f"Доступные таблицы: {tables}")

# Определяем таблицы
school_table = Table('schools_school', meta, autoload_with=engine)
# Пытаемся загрузить таблицу
newsletterTemplate_table = Table('schools_newslettertemplate', meta, autoload_with=engine)
sentNewsletter_table = Table('schools_sentnewsletter', meta, autoload_with=engine)
