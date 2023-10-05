import os
import zipfile
from datetime import datetime

from config.config import CONTAINER_NAME
from config.selectel_client import SelectelClient
from loguru import logger

selectel_client = SelectelClient()


def compress_and_upload_backup(backup_path, db_name):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_file_path = f"{db_name}_{timestamp}.zip"

        # Сжимаем бэкап
        with zipfile.ZipFile(zip_file_path, "w") as zip_file:
            zip_file.write(backup_path)

        # Загружаем в Selectel
        with open(zip_file_path, "rb") as f:
            selectel_client.upload_to_selectel(f"/{db_name}/{zip_file_path}", f.read())
            logger.info(f"Successfully compressed and uploaded database backup")
    except Exception as e:
        logger.error(f"Error compressing and uploading database backup: {e}")
    finally:
        # Удаляем локальные файлы
        os.remove(backup_path)
        os.remove(zip_file_path)


def delete_old_backups(db_name, max_backups=7):
    try:
        # Получаем список файлов бэкапов
        files = selectel_client.get_folder_files(f"/{db_name}/", "_segments")
    except Exception as e:
        logger.debug(
            f"{e} The errors were caused by trying to connect to Selectel Cloud Storage"
        )
    logger.debug(f"Has {len(files)} backups")
    # Сортируем по дате изменения
    sorted_files = sorted(files, key=lambda f: f["last_modified"], reverse=True)
    num_backups = len(sorted_files)
    logger.debug(f"Has {num_backups} backups")

    # Удаляем старые бэкапы, если их больше максимального лимита
    if len(sorted_files) > max_backups:
        logger.debug(f"Deleting old backups")
        for f in sorted_files[max_backups:]:
            selectel_client.remove_from_selectel(f)
