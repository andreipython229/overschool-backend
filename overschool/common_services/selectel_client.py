import hmac
import io
from datetime import datetime
from hashlib import sha1
from time import time

import redis
import requests
from django.core.files.base import ContentFile, File
from PIL import Image

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
        host=REDIS_HOST,
        # host="localhost",
        port=REDIS_PORT,
        db=0,
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

    # Запрос на загрузку файла либо сегмента файла
    @staticmethod
    def upload_request(path, token, data, disposition, content_type=None):
        return requests.put(
            SelectelClient.URL + path,
            headers={
                "X-Auth-Token": token,
                "Content-Type": content_type,
                "Content-Disposition": disposition,
            },
            data=data,
        )

    # Сжатие изображения
    @staticmethod
    def get_compressed_image(img):
        image = Image.open(img)
        image_io = io.BytesIO()
        image.save(image_io, format=image.format, quality=20, optimize=True)
        return image_io.getvalue()

    # Загрузка файла непосредственно в хранилище
    def upload_to_selectel(self, path, file, disposition="attachment"):
        if file.size <= 10 * 1024 * 1024:
            if file.content_type.startswith("image") and file.size >= 300 * 1024:
                file_data = self.get_compressed_image(file)
            else:
                file_data = file.read()

            try:
                r = self.upload_request(
                    path,
                    self.REDIS_INSTANCE.get("selectel_token"),
                    file_data,
                    disposition,
                    file.content_type,
                )
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    self.upload_request(
                        path,
                        self.get_token(),
                        file_data,
                        disposition,
                        file.content_type,
                    )
        else:
            # Сегментированная загрузка большого файла (сегменты загружаются в служебный контейнер)
            for num, chunk in enumerate(file.chunks(chunk_size=10 * 1024 * 1024)):
                try:
                    r = self.upload_request(
                        "_segments"
                        + path
                        + "/{}{}".format((4 - len(str(num + 1))) * "0", num + 1),
                        self.REDIS_INSTANCE.get("selectel_token"),
                        chunk,
                        disposition,
                    )
                    r.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        self.upload_request(
                            "_segments"
                            + path
                            + "/{}{}".format((4 - len(str(num + 1))) * "0", num + 1),
                            self.get_token(),
                            chunk,
                            disposition,
                        )
            # Создание файла-манифеста в основном контейнере (под именем загружаемого файла)
            requests.put(
                self.URL + path,
                headers={
                    "X-Auth-Token": self.REDIS_INSTANCE.get("selectel_token"),
                    "X-Object-Manifest": "{}_segments{}/".format(
                        CONTAINER_NAME, path
                    ).encode(encoding="UTF-8", errors="strict"),
                },
            )

    def upload_file(self, uploaded_file, base_lesson, disposition="attachment"):
        course = base_lesson.section.course
        course_id = course.course_id
        school_id = course.school.school_id
        file_path = "/{}_school/{}_course/{}_lesson/{}@{}".format(
            school_id, course_id, base_lesson.id, datetime.now(), uploaded_file.name
        ).replace(" ", "_")
        self.upload_to_selectel(file_path, uploaded_file, disposition)
        return file_path

    def upload_school_image(self, uploaded_image, school_id):
        file_path = "/{}_school/school_data/images/{}@{}".format(
            school_id, datetime.now(), uploaded_image.name
        ).replace(" ", "_")
        self.upload_to_selectel(file_path, uploaded_image)
        return file_path

    def upload_course_image(self, uploaded_image, course):
        course_id = course.course_id
        school_id = course.school.school_id
        file_path = "/{}_school/{}_course/{}@{}".format(
            school_id, course_id, datetime.now(), uploaded_image.name
        ).replace(" ", "_")
        self.upload_to_selectel(file_path, uploaded_image)
        return file_path

    def upload_user_avatar(self, avatar, user_id):
        file_path = "/users/avatars/{}@{}".format(user_id, avatar.name).replace(
            " ", "_"
        )
        self.upload_to_selectel(file_path, avatar)
        return file_path

    # Запрос на удаление файла
    @staticmethod
    def remove_request(file_path, token):
        return requests.delete(
            SelectelClient.URL + file_path,
            headers={"X-Auth-Token": token},
        )

    # Удаление файла из хранилища
    def remove_from_selectel(self, file_path):
        try:
            r = self.remove_request(
                file_path, self.REDIS_INSTANCE.get("selectel_token")
            )
            r.raise_for_status()
            return "Success"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == "401":
                try:
                    r = self.remove_request(file_path, self.get_token())
                    r.raise_for_status()
                    return "Success"
                except requests.exceptions.HTTPError:
                    return "Error"
            else:
                return "Error"

    # Запрос на удаление нескольких файлов
    @staticmethod
    def bulk_remove_request(token, data):
        return requests.post(
            SelectelClient.BASE_URL + "?bulk-delete=true",
            headers={
                "X-Auth-Token": token,
                "Content-Type": "text/plain",
            },
            data=data.encode("utf-8"),
        )

    # Удаление сразу нескольких файлов из хранилища
    def bulk_remove_from_selectel(self, files, segments=""):
        data = ""
        for file_path in files:
            data += CONTAINER_NAME + segments + file_path + "\n"
        try:
            r = self.bulk_remove_request(
                self.REDIS_INSTANCE.get("selectel_token"), data
            )
            r.raise_for_status()
            return "Success"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == "401":
                try:
                    r = self.bulk_remove_request(self.get_token(), data)
                    r.raise_for_status()
                    return "Success"
                except requests.exceptions.HTTPError:
                    return "Error"
            else:
                return "Error"

    # Получение ссылки на файл
    def get_selectel_link(self, file_path):
        sig, expires = self.create_access_key(CONTAINER_KEY, file_path)
        link = (
            self.URL
            + file_path
            + "?temp_url_sig={}&temp_url_expires={}".format(sig, expires)
        )
        return link

    # Запрос на получение списка файлов
    @staticmethod
    def get_folder_files_request(segments, folder, token):
        return requests.get(
            SelectelClient.URL + segments + "/?format=json&prefix={}".format(folder),
            headers={"X-Auth-Token": token},
        )

    # Получение списка файлов, путь к которым начинается с указанного префикса
    def get_folder_files(self, folder, segments=""):
        objects = None
        try:
            objects = self.get_folder_files_request(
                segments, folder, self.REDIS_INSTANCE.get("selectel_token")
            )
            objects.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                objects = self.get_folder_files_request(
                    segments, folder, self.get_token()
                )
        files = (
            list(map(lambda el: "/" + el["name"], objects.json())) if objects else None
        )
        return files
