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
    username = email_for_password
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

    # Создаем юзера, если его еще нет
    user_id = db_handler.execute_query(
        "WITH new_row AS ("
        "INSERT INTO users_user (username, email, first_name, last_name, password, is_superuser, is_staff, is_active, "
        "date_joined, last_login) SELECT %(username)s, %(email)s, %(first_name)s, %(last_name)s, %(password)s, "
        "%(is_superuser)s, %(is_staff)s, %(is_active)s, %(date_joined)s, %(last_login)s WHERE NOT EXISTS "
        "(SELECT * FROM users_user WHERE username=%(username)s AND email=%(email)s) RETURNING id)"
        "SELECT id FROM new_row UNION "
        "SELECT id FROM users_user WHERE username=%(username)s AND email=%(email)s",
        flat=True,
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password,
        is_superuser=False,
        is_staff=False,
        is_active=False,
        data_joined=date_joined,
        last_login=last_login,
    )["id"]

    # Получаем роль студента
    role_id = db_handler.execute_query(
        "WITH new_row AS ("
        "INSERT INTO auth_group (name) SELECT %(role_name)s WHERE NOT EXISTS "
        "(SELECT * FROM auth_group WHERE name=%(role_name)s) RETURNING id)"
        "SELECT id FROM new_row UNION "
        "SELECT id FROM auth_group WHERE name=%(role_name)s",
        flat=True,
        role_name="Student",
    )["id"]

    # Добавляем юзеру роль студента
    _ = db_handler.execute_query(
        "INSERT INTO users_user_groups (user_id, group_id) SELECT %(user_id)s, %(role_id)s WHERE NOT EXISTS "
        "(SELECT * FROM users_user_groups WHERE user_id=%(user_id)s AND role_id=%(role_id)s) RETURNING id",
        flat=True,
        user_id=user_id,
        role_id=role_id,
    )

    for course, progress in zip(courses, progresses):
        course_name, group_name = re.match(r"(\w+)\s\((\w+)\)", course)
        progress = float(re.match(r"(\d+\.\d+)\%", progress).group(0))

        # Получаем курс со списком уроков
        course_with_lessons = db_handler.execute_query(
            "SELECT _course.course_id, array_agg(_lesson.lesson_id ORDER BY _lesson.order) lessons"
            "FROM public.courses_lesson _lesson"
            "INNER JOIN public.courses_section _section ON _lesson.section_id=_section.section_id"
            "INNER JOIN public.courses_course _course ON _section.course_id=_course.course_id"
            "WHERE _course.name=%(course_name)s"
            "GROUP BY _course.course_id"
            "ORDER BY _course.course_id",
            flat=True,
            course_name=course_name,
        )

        # Получаем группу по курсу и названию
        coursegroup_id = db_handler.execute_query(
            "SELECT _group.group_id FROM courses_coursegroup _group WHERE _group.name=%(group_name)s AND "
            "_group.course_id=%(course_id)s",
            flat=True,
            group_name=group_name,
            course_id=course_with_lessons["course_id"],
        )["group_id"]

        # Добавляем юзера в группу
        _ = db_handler.execute_query(
            "INSERT INTO courses_coursegroup_students(coursegroup_id, user_id) SELECT %(coursegroup_id)s, %(user_id)s "
            "WHERE NOT EXISTS (SELECT * FROM courses_coursegroup_students WHERE coursegroup_id=%(coursegroup_id)s AND "
            "user_id=%(user_id)s) RETURNING id",
            flat=True,
            coursegroup_id=coursegroup_id,
            user_id=user_id,
        )

        # Получаем текущий урок на курсе по прогрессу
        lesson_id = course_with_lessons["lessons"][math.ceil(len(course_with_lessons["lessons"]) / 100.0 * progress)]

        # Добавляем юзеру текущий урок (восстанавливаем его прогресс)
        _ = db_handler.execute_query(
            "INSERT INTO courses_userprogress (user_id,lesson_id) SELECT %(user_id)s, %(lesson_id)s "
            "WHERE NOT EXISTS (SELECT * FROM courses_userprogress WHERE user_id=%(user_id)s AND "
            "lesson_id=%(lesson_id)s) RETURNING user_progress_id",
            flat=True,
            user_id=user_id,
            lesson_id=lesson_id,
        )
