import csv
from datetime import datetime

import psycopg2
import psycopg2.extras


class DBHandler:
    def __init__(self, **kwargs) -> None:
        self.user = kwargs["USER"]
        self.password = kwargs["PASSWORD"]
        self.host = kwargs["HOST"]
        self.port = kwargs["PORT"]
        self.database = kwargs["NAME"]

    def execute_query(self, query: str, *params):
        with psycopg2.connect(
            user=self.user, password=self.password, host=self.host, port=self.port, database=self.database
        ) as connection:
            with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, (params))
                return cursor.fetchall()

    def load_students(self, csv_file_name: str):
        with psycopg2.connect(
            user=self.user, password=self.password, host=self.host, port=self.port, database=self.database
        ) as connection:
            with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                with open(csv_file_name, "r", newline="", encoding="utf-8-sig") as file:
                    reader = csv.DictReader(file, delimiter=";")
                    for row in reader:
                        email = row["Почта"]
                        email_for_password, _ = email.split("@")
                        password = email_for_password + "password"
                        if row["Имя"] == "Без имени":
                            first_name, last_name, patronymic = "", "", ""
                        else:
                            ws_count = row["Имя"].count(" ")
                            if ws_count == 1:
                                first_name, last_name, patronymic = row["Имя"], "", ""
                            elif ws_count == 2:
                                first_name, last_name, patronymic = row["Имя"].split(), ""
                            elif ws_count == 3:
                                first_name, last_name, patronymic = row["Имя"].split()
                        last_login = row["Был(а) онлайн"]
                        if not last_login:
                            last_login = None
                        date_joined = row["Добавлен"]
                        courses = row["Курсы"].split(",")
                        cursor.execute(
                            "INSERT INTO users_user(email,first_name,last_name,password,is_superuser,"
                            "is_staff,is_active,date_joined,last_login)"
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                            "RETURNING user_id",
                            (
                                email,
                                first_name,
                                last_name,
                                password,
                                False,
                                False,
                                False,
                                date_joined,
                                last_login,
                            ),
                        )
                        print(cursor.fetchone())
                        cursor.execute(
                            "SELECT course_id FROM courses_course WHERE name in %s",
                            (tuple(courses),),
                        )
                        print([fields for fields in cursor.fetchall()])
