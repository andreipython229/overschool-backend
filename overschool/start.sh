#!/bin/bash

# Сбор статических файлов
python manage.py collectstatic --noinput

# Создание миграций (если необходимо)
python manage.py makemigrations

# Применение миграций
python manage.py migrate

# Запуск Huey
python manage.py run_huey &

# Запуск Daphne
daphne -b 0.0.0.0 -p 8000 overschool.asgi:application
