import requests
from overschool.celery import app
from users.services import *


@app.task
def send_code_to_phone(url: str, params: dict, method: str):
    requests.request(method,
                     url,
                     params=params,
                     headers={"content-type": "application/json"},
                     )
