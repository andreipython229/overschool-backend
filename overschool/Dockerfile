FROM python:3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY . .

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# Копируем скрипт start.sh в образ
COPY start.sh /start.sh

# Даем права на выполнение скрипту
RUN chmod +x /start.sh

# Указываем команду для запуска контейнера
CMD ["/start.sh"]
