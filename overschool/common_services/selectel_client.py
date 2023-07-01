import hmac
from datetime import datetime
from hashlib import sha1
from time import time

import redis
import requests

from overschool.settings import (
    ACCOUNT_ID,
    CONTAINER_KEY,
    CONTAINER_NAME,
    REDIS_HOST,
    REDIS_PORT,
    SEL_AUTH_KEY,
)

base_url = "https://api.selcdn.ru/v1/SEL_{}".format(ACCOUNT_ID)
url = base_url + "/{}".format(CONTAINER_NAME)

REDIS_INSTANCE = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    password="sOmE_sEcUrE_pAsS",
)

auth_token = REDIS_INSTANCE.get("selectel_token")


# Получение токена для работы с хранилищем
def get_token():
    resp = requests.get(
        "https://api.selcdn.ru/auth/v1.0",
        headers={"X-Auth-User": ACCOUNT_ID, "X-Auth-Key": SEL_AUTH_KEY},
    )
    token = resp.headers.get("X-Auth-Token")
    REDIS_INSTANCE.set("selectel_token", token)
    return token


# Создание ключа доступа, используемого в ссылке к файлу
def create_access_key(secret_key, file):
    method = "GET"
    # ссылка будет действительна 3 дня
    expires = int(time()) + 259200
    # путь к файлу в хранилище
    path = "/v1/SEL_{}/{}{}".format(ACCOUNT_ID, CONTAINER_NAME, file)
    # секретный ключ контейнера
    link_secret_key = str.encode(secret_key)
    # генерируем ключ доступа к файлу
    hmac_body = str.encode("{}\n{}\n{}".format(method, expires, path))
    # итоговый ключ доступа
    sig = hmac.new(link_secret_key, hmac_body, sha1).hexdigest()
    return sig, expires


def upload_to_selectel(path, file):
    try:
        r = requests.put(
            url + path, headers={"X-Auth-Token": auth_token}, files={"file": file}
        )
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            requests.put(
                url + path, headers={"X-Auth-Token": get_token()}, files={"file": file}
            )


def upload_file(uploaded_file, base_lesson):
    course = base_lesson.section.course
    course_id = course.course_id
    school_id = course.school.school_id
    file_path = "/{}_school/{}_course/{}_lesson/{}_{}".format(
        school_id, course_id, base_lesson.id, datetime.now(), uploaded_file.name
    ).replace(" ", "_")
    upload_to_selectel(file_path, uploaded_file)
    return file_path


def upload_school_image(uploaded_image, school_id):
    file_path = "/{}_school/school_data/images/{}_{}".format(
        school_id, datetime.now(), uploaded_image.name
    ).replace(" ", "_")
    upload_to_selectel(file_path, uploaded_image)
    return file_path


def upload_course_image(uploaded_image, course):
    course_id = course.course_id
    school_id = course.school.school_id
    file_path = "/{}_school/{}_course/{}_{}".format(
        school_id, course_id, datetime.now(), uploaded_image.name
    ).replace(" ", "_")
    upload_to_selectel(file_path, uploaded_image)
    return file_path


def upload_user_avatar(avatar, user_id):
    file_path = "/users/avatars/{}_{}".format(user_id, avatar.name).replace(" ", "_")
    upload_to_selectel(file_path, avatar)
    return file_path


def remove_from_selectel(file_path):
    try:
        r = requests.delete(url + file_path, headers={"X-Auth-Token": auth_token})
        r.raise_for_status()
        return "Success"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == "401":
            try:
                r = requests.delete(
                    url + file_path, headers={"X-Auth-Token": get_token()}
                )
                r.raise_for_status()
                return "Success"
            except requests.exceptions.HTTPError:
                return "Error"
        else:
            return "Error"


def bulk_remove_from_selectel(files):
    data = ""
    for file_path in files:
        data += CONTAINER_NAME + file_path + "\n"
    try:
        r = requests.post(
            base_url + "?bulk-delete=true",
            headers={"X-Auth-Token": auth_token, "Content-Type": "text/plain"},
            data=data.encode("utf-8"),
        )
        r.raise_for_status()
        return "Success"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == "401":
            try:
                r = requests.post(
                    base_url + "?bulk-delete=true",
                    headers={"X-Auth-Token": get_token(), "Content-Type": "text/plain"},
                    data=data.encode("utf-8"),
                )
                r.raise_for_status()
                return "Success"
            except requests.exceptions.HTTPError:
                return "Error"
        else:
            return "Error"


def get_selectel_link(file_path):
    sig, expires = create_access_key(CONTAINER_KEY, file_path)
    link = url + file_path + "?temp_url_sig={}&temp_url_expires={}".format(sig, expires)
    return link
