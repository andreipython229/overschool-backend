FROM python:3.11

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /code

# Копируем все файлы в контейнер
COPY . .

# Обновляем pip и устанавливаем зависимости из requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
