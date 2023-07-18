import requests
from config.config import (
    ACCOUNT_ID,
    CONTAINER_KEY,
    CONTAINER_NAME,
    REDIS_HOST,
    REDIS_PORT,
)


class SelectelClient:
    BASE_URL = "https://api.selcdn.ru/v1/SEL_{}".format(ACCOUNT_ID)
    URL = BASE_URL + "/{}".format(CONTAINER_NAME)

    # Получение токена для работы с хранилищем
    def get_token(self):
        resp = requests.get(
            "https://api.selcdn.ru/auth/v1.0",
            headers={"X-Auth-User": ACCOUNT_ID, "X-Auth-Key": CONTAINER_KEY},
        )
        token = resp.headers.get("X-Auth-Token")
        return token

    # Загрузка файла непосредственно в хранилище
    def upload_to_selectel(self, path, file):
        token = self.get_token()

        if file.size <= 90 * 1024 * 1024:
            file_data = file.read()
            try:
                r = self.upload_request(path, token, file_data, file.content_type)
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    token = self.get_token()
                    self.upload_request(path, token, file_data, file.content_type)
        else:
            # Сегментированная загрузка большого файла (сегменты загружаются в служебный контейнер)
            for num, chunk in enumerate(file.chunks(chunk_size=90 * 1024 * 1024)):
                try:
                    r = self.upload_request(
                        "_segments" + path + "/{}".format(num + 1), token, chunk
                    )
                    r.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        token = self.get_token()
                        self.upload_request(
                            "_segments" + path + "/{}".format(num + 1), token, chunk
                        )
            # Создание файла-манифеста в основном контейнере (под именем загружаемого файла)
            requests.put(
                self.URL + path,
                headers={
                    "X-Auth-Token": token,
                    "X-Object-Manifest": "{}_segments{}/".format(CONTAINER_NAME, path),
                },
            )

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

    # Запрос на удаление файла
    @staticmethod
    def remove_request(file_path, token):
        return requests.delete(
            SelectelClient.URL + file_path,
            headers={"X-Auth-Token": token},
        )
