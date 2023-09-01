import os
from datetime import datetime

import zipfile

from config.config import CONTAINER_NAME
from config.selectel_client import SelectelClient

selectel_client = SelectelClient()


def compress_and_upload_backup(backup_path, db_name):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_file_path = f"{db_name}_{timestamp}.zip"

    # Сжимаем бэкап
    with zipfile.ZipFile(zip_file_path, "w") as zip_file:
        zip_file.write(backup_path)

    # Загружаем в Selectel
    with open(zip_file_path, "rb") as f:
        selectel_client.upload_to_selectel(
            f"{CONTAINER_NAME}/{db_name}/{zip_file_path}",
            f.read()
        )

    # Удаляем локальные файлы
    os.remove(backup_path)
    os.remove(zip_file_path)


def delete_old_backups(db_name, max_backups=7):
    # Получаем список файлов бэкапов
    files = selectel_client.get_folder_files(f"{CONTAINER_NAME}/{db_name}/")

    # Сортируем по дате изменения
    sorted_files = sorted(files, key=lambda f: f['last_modified'], reverse=True)

    # Удаляем старые бэкапы, если их больше максимального лимита
    if len(sorted_files) > max_backups:
        for f in sorted_files[max_backups:]:
            selectel_client.remove_from_selectel(f)
