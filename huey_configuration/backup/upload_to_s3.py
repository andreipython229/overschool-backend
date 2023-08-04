import os
import subprocess
import zipfile

from config.config import CONTAINER_NAME
from config.selectel_client import SelectelClient
from loguru import logger

selectel_client = SelectelClient()


def compress_and_upload(backup_path, zip_file_path, db):
    try:
        # Compress backup file into a zip archive
        with zipfile.ZipFile(zip_file_path, "w") as zip_file:
            zip_file.write(backup_path)
        file_size = os.path.getsize(zip_file_path)
        # Upload compressed backup file to Selectel Cloud Storage
        with open(zip_file_path, 'rb') as f:
            selectel_client.upload_to_selectel(
                f"{CONTAINER_NAME}/{db}/{zip_file_path}",
                f,
                file_size
            )
    except Exception as e:
        logger.error(f"Error compressing and uploading {db} database backup: {e}")
    finally:
        # Clean up backup and zip files
        subprocess.run(["rm", backup_path])
        subprocess.run(["rm", zip_file_path])

    # Delete old backup files if the limit of 7 is exceeded
    try:
        objects = selectel_client.get_folder_files(f"{db}/")
    except Exception as e:
        objects = []
        logger.debug(
            f"{e} The errors were caused by trying to connect to Selectel Cloud Storage"
        )
    object_list = sorted(objects, key=lambda obj: obj["last_modified"], reverse=True)
    num_backups = len(object_list)
    logger.debug(f"{db} has {num_backups} backups")

    if num_backups > 7:
        logger.debug(f"Deleting old backups for {db}")
        for obj in object_list[7:]:
            selectel_client.remove_from_selectel(f"{CONTAINER_NAME}/{db}/{obj['name']}")

    # Delete temporary files
    subprocess.run(["rm", backup_path])
    subprocess.run(["rm", zip_file_path])
