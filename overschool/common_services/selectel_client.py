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


class SelectelClient:
    BASE_URL = "https://api.selcdn.ru/v1/SEL_{}".format(ACCOUNT_ID)
    URL = BASE_URL + "/{}".format(CONTAINER_NAME)
    REDIS_INSTANCE = redis.StrictRedis(
        # host=REDIS_HOST,
        host="localhost",
        port=REDIS_PORT,
        db=0,
        password="sOmE_sEcUrE_pAsS",
    )

    # Получение токена для работы с хранилищем
    def get_token(self):
        resp = requests.get(
            "https://api.selcdn.ru/auth/v1.0",
            headers={"X-Auth-User": ACCOUNT_ID, "X-Auth-Key": SEL_AUTH_KEY},
        )
        token = resp.headers.get("X-Auth-Token")
        self.REDIS_INSTANCE.set("selectel_token", token)
        return token

    # Создание ключа доступа, используемого в ссылке к файлу
    @staticmethod
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

    def upload_to_selectel(self, path, file):
        try:
            r = requests.put(
                self.URL + path,
                headers={
                    "X-Auth-Token": self.REDIS_INSTANCE.get("selectel_token"),
                    "Content-Type": file.content_type,
                    "Content-Disposition": "attachment",
                },
                data=file.read(),
            )
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                requests.put(
                    self.URL + path,
                    headers={
                        "X-Auth-Token": self.get_token(),
                        "Content-Type": file.content_type,
                        "Content-Disposition": "attachment",
                    },
                    data=file.read(),
                )

    def upload_file(self, uploaded_file, base_lesson):
        course = base_lesson.section.course
        course_id = course.course_id
        school_id = course.school.school_id
        file_path = "/{}_school/{}_course/{}_lesson/{}_{}".format(
            school_id, course_id, base_lesson.id, datetime.now(), uploaded_file.name
        ).replace(" ", "_")
        self.upload_to_selectel(file_path, uploaded_file)
        return file_path

    def upload_school_image(self, uploaded_image, school_id):
        file_path = "/{}_school/school_data/images/{}_{}".format(
            school_id, datetime.now(), uploaded_image.name
        ).replace(" ", "_")
        self.upload_to_selectel(file_path, uploaded_image)
        return file_path

    def upload_course_image(self, uploaded_image, course):
        course_id = course.course_id
        school_id = course.school.school_id
        file_path = "/{}_school/{}_course/{}_{}".format(
            school_id, course_id, datetime.now(), uploaded_image.name
        ).replace(" ", "_")
        self.upload_to_selectel(file_path, uploaded_image)
        return file_path

    def upload_user_avatar(self, avatar, user_id):
        file_path = "/users/avatars/{}_{}".format(user_id, avatar.name).replace(
            " ", "_"
        )
        self.upload_to_selectel(file_path, avatar)
        return file_path

    def remove_from_selectel(self, file_path):
        try:
            r = requests.delete(
                self.URL + file_path,
                headers={"X-Auth-Token": self.REDIS_INSTANCE.get("selectel_token")},
            )
            r.raise_for_status()
            return "Success"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == "401":
                try:
                    r = requests.delete(
                        self.URL + file_path, headers={"X-Auth-Token": self.get_token()}
                    )
                    r.raise_for_status()
                    return "Success"
                except requests.exceptions.HTTPError:
                    return "Error"
            else:
                return "Error"

    def bulk_remove_from_selectel(self, files):
        data = ""
        for file_path in files:
            data += CONTAINER_NAME + file_path + "\n"
        try:
            r = requests.post(
                self.BASE_URL + "?bulk-delete=true",
                headers={
                    "X-Auth-Token": self.REDIS_INSTANCE.get("selectel_token"),
                    "Content-Type": "text/plain",
                },
                data=data.encode("utf-8"),
            )
            r.raise_for_status()
            return "Success"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == "401":
                try:
                    r = requests.post(
                        self.BASE_URL + "?bulk-delete=true",
                        headers={
                            "X-Auth-Token": self.get_token(),
                            "Content-Type": "text/plain",
                        },
                        data=data.encode("utf-8"),
                    )
                    r.raise_for_status()
                    return "Success"
                except requests.exceptions.HTTPError:
                    return "Error"
            else:
                return "Error"

    def get_selectel_link(self, file_path):
        sig, expires = self.create_access_key(CONTAINER_KEY, file_path)
        link = (
            self.URL
            + file_path
            + "?temp_url_sig={}&temp_url_expires={}".format(sig, expires)
        )
        return link

    def get_folder_files(self, folder):
        objects = None
        try:
            objects = requests.get(
                self.URL + "/?format=json&prefix={}".format(folder),
                headers={"X-Auth-Token": self.REDIS_INSTANCE.get("selectel_token")},
            )
            objects.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                objects = requests.get(
                    self.URL + "/?format=json&prefix={}".format(folder),
                    headers={"X-Auth-Token": self.get_token()},
                )
        files = (
            list(map(lambda el: "/" + el["name"], objects.json())) if objects else None
        )
        return files
