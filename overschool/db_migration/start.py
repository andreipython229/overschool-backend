import math
import re
import sys
from pathlib import Path

from environ import Env

from handlers import CSVHandler, DBHandler

BASE_DIR = Path(__file__).resolve().parent.parent
env = Env()
Env.read_env(str(BASE_DIR / ".env"))

# Хэндлеры базы данных проекта и csv файла
db_handler = DBHandler(**env.db_url("DB_URL"))
csv_handler = CSVHandler()

# Читаем из csv список студентов
students = list(csv_handler.load_from(sys.argv[1]))

for student in students:
    # Получаем данные из студента, подгоняя логику под нашу бд
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
    courses = student["Курсы"].split(";")
    progresses = student["Прогресс по курсам"].split(";")

    # Создаем юзера и возвращаем его id
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
        flat=True,
    )["user_id"]

    # Получаем id роли студента
    role_id = db_handler.execute_query("SELECT id FROM auth_group WHERE name=%s", "Student", flat=True)["id"]

    # Добавляем юзеру роль студента
    _ = db_handler.execute_query(
        "INSERT INTO users_user_groups(user_id,group_id) VALUES (%s,%s) RETURNING id", user_id, role_id, flat=True
    )

    for course, progress in zip(courses, progresses):
        course_name, group_name = re.match(r"(\w+)\s\((\w+)\)", course)
        progress = float(re.match(r"(\d+\.\d+)\%", progress).group(0))

        # Получаем id курса со списком ids уроков
        course_with_lessons = db_handler.execute_query(
            "SELECT _course.course_id, array_agg(_lesson.lesson_id ORDER BY _lesson.order) lessons"
            "FROM public.courses_lesson _lesson"
            "INNER JOIN public.courses_section _section ON _lesson.section_id=_section.section_id"
            "INNER JOIN public.courses_course _course ON _section.course_id=_course.course_id"
            "WHERE _course.name=%s"
            "GROUP BY _course.course_id"
            "ORDER BY _course.course_id",
            course_name,
            flat=True,
        )

        # Получаем id группы по курсу и названию
        coursegroup_id = db_handler.execute_query(
            "SELECT _group.group_id FROM courses_coursegroup _group WHERE _group.name=%s AND _group.course_id=%s",
            group_name,
            course_with_lessons["course_id"],
            flat=True,
        )["group_id"]

        # Добавляем юзера в группу
        _ = db_handler.execute_query(
            "INSERT INTO courses_coursegroup_students(coursegroup_id, user_id) VALUES (%s,%s) RETURNING id",
            coursegroup_id,
            user_id,
            flat=True,
        )

        # Получаем id текущего урока на курсе по прогрессу
        lesson_id = course_with_lessons["lessons"][math.ceil(len(course_with_lessons["lessons"]) / 100.0 * progress)]

        # Добавляем юзеру текущий урок (восстанавливаем его прогресс)
        _ = db_handler.execute_query(
            "INSERT INTO courses_userprogress(user_id,lesson_id) VALUES (%s,%s) RETURNING user_progress_id",
            user_id,
            lesson_id,
            flat=True,
        )
