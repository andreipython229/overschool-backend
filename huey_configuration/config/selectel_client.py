import redis
import requests
from config.config import (
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
        port=REDIS_PORT,
        db=3,
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

    # Запрос на загрузку файла либо сегмента файла
    @staticmethod
    def upload_request(path, token, data, content_type=None):
        return requests.put(
            SelectelClient.URL + path,
            headers={
                "X-Auth-Token": token,
                "Content-Type": content_type,
                "Content-Disposition": "attachment",
            },
            data=data,
        )

    # Загрузка файла непосредственно в хранилище
    def upload_to_selectel(self, path, file, size):

        if isinstance(file, bytes):
            file_size = size
            file_data = file
        elif hasattr(file, 'size'):
            file_size = file.size
            file_data = file.read()
        else:
            raise ValueError('Invalid file type')
        if file_size <= 90 * 1024 * 1024:
            try:
                r = self.upload_request(
                    path,
                    self.REDIS_INSTANCE.get("selectel_token"),
                    file_data,
                    file.content_type,
                )
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    self.upload_request(
                        path, self.get_token(), file_data, file.content_type
                    )
        else:

            if isinstance(file, bytes):
                self.upload_request(path, self.get_token(), file)
            else:
                CHUNK_SIZE = 90 * 1024 * 1024
                # Сегментированная загрузка файла
                for num in range(0, len(file_data), CHUNK_SIZE):
                    chunk = file_data[num:num + CHUNK_SIZE]
                    try:
                        self.upload_request(
                            "_segments" + path + "/{}".format(num + 1),
                            self.REDIS_INSTANCE.get("selectel_token"),
                            chunk
                        )
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 401:
                            self.upload_request(
                                "_segments" + path + "/{}".format(num + 1),
                                self.get_token(),
                                chunk
                            )
            # Создание файла-манифеста в основном контейнере (под именем загружаемого файла)
            requests.put(
                self.URL + path,
                headers={
                    "X-Auth-Token": self.REDIS_INSTANCE.get("selectel_token"),
                    "X-Object-Manifest": "{}_segments{}/".format(CONTAINER_NAME, path),
                },
            )

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
