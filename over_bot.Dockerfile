# Используем базовый образ Python
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию в контейнере
WORKDIR /code

# Копируем requirements.txt в контейнер
COPY over_bot .

# Устанавливаем зависимости из requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Команда для запуска бота
CMD python3 main.py
