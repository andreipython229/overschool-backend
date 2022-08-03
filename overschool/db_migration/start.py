import os
import sys
from pathlib import Path

import psycopg2
from environ import Env

from handlers import CSVHandler, DBHandler

BASE_DIR = Path(__file__).resolve().parent.parent
env = Env()
Env.read_env(str(BASE_DIR / ".env"))

db_handler = DBHandler(**env.db_url("DB_URL"))
csv_handler = CSVHandler()

students = list(csv_handler.load_from(sys.argv[1]))
for student in students:
    email = student["Почта"]
    email_for_password, _ = email.split("@")
    password = email_for_password + "password"
    if student["Имя"] == "Без имени":
        first_name, last_name, patronymic = "", "", ""
    else:
        ws_count = student["Имя"].count(" ")
        if ws_count == 1:
            first_name, last_name, patronymic = student["Имя"], "", ""
        elif ws_count == 2:
            first_name, last_name, patronymic = student["Имя"].split(), ""
        elif ws_count == 3:
            first_name, last_name, patronymic = student["Имя"].split()
    last_login = student["Был(а) онлайн"]
    if not last_login:
        last_login = None
    date_joined = student["Добавлен"]
    courses_names = student["Курсы"].split(",")
    user_id = db_handler.execute_query(
        "INSERT INTO users_user(email,first_name,last_name,password,is_superuser, is_staff,is_active,date_joined,last_login)"
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING user_id",
        email,
        first_name,
        last_name,
        password,
        False,
        False,
        False,
        date_joined,
        last_login,
    )
    print(user_id)
    courses_ids = db_handler.execute_query(
        "SELECT course_id FROM courses_course WHERE name in %s", (tuple(courses_names),)
    )
    print(courses_ids)
    role_id = db_handler.execute_query("SELECT id FROM auth_group WHERE name=%s", "Student")[0]
    print(role_id)
    user_role_id = db_handler.execute_query(
        "INSERT INTO users_user_groups(user_id,group_id) VALUES (%s,%s) RETURNING id", user_id, role_id
    )
