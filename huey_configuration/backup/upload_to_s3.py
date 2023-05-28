import subprocess
import zipfile

from config.config import (
    CLIENT_ID,
    YANDEX_DISK_UPLOAD_PATH,
    YANDEX_SECRET,
    YANDEX_TOKEN,
)
from loguru import logger
from yadisk import YaDisk

yadisk = YaDisk(CLIENT_ID, YANDEX_SECRET, YANDEX_TOKEN)


def compress_and_upload(backup_path, zip_file_path, db):
    try:
        # Compress backup file into a zip archive
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(backup_path)

        # Upload compressed backup file to Yandex Disk
        yadisk.upload(zip_file_path, f"{YANDEX_DISK_UPLOAD_PATH}/{db}/{zip_file_path}")
    except Exception as e:
        logger.error(f"Error compressing and uploading {db} database backup: {e}")
    finally:
        # Clean up backup and zip files
        subprocess.run(["rm", backup_path])
        subprocess.run(["rm", zip_file_path])

    # Delete old backup files if the limit of 4 is exceeded
    try:
        objects = yadisk.listdir(f"{YANDEX_DISK_UPLOAD_PATH}/{db}/")
    except Exception as e:
        objects = []
        logger.debug(f"{e} The errors were caused by trying to connect to Yandex Disk")
    object_list = sorted(objects, key=lambda obj: obj.modified, reverse=True)
    num_backups = len(object_list)
    logger.debug(f"{db} has {num_backups} backups")

    if num_backups > 4:
        logger.debug(f"Deleting old backups for {db}")
        for obj in object_list[4:]:
            yadisk.remove(f"{YANDEX_DISK_UPLOAD_PATH}/{db}/{obj.name}")

    # Delete temporary files
    subprocess.run(["rm", backup_path])
    subprocess.run(["rm", zip_file_path])
