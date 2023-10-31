import os
import zipfile
from datetime import datetime

import boto3
from config.config import (
    ENDPOINT_URL,
    REGION_NAME,
    S3_ACCESS_KEY,
    S3_BUCKET,
    S3_SECRET_KEY,
)
from loguru import logger

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    region_name=REGION_NAME,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)


def compress_and_upload_backup(backup_path, db_name):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_file_path = f"{db_name}_{timestamp}.zip"

        # Сжимаем бэкап
        with zipfile.ZipFile(zip_file_path, "w") as zip_file:
            zip_file.write(backup_path)

        # Загружаем в Selectel
        s3.upload_file(
            Filename=zip_file_path, Bucket=S3_BUCKET, Key=f"{db_name}/{zip_file_path}"
        )
        logger.info(f"Successfully compressed and uploaded database backup")
    except Exception as e:
        logger.error(f"Error compressing and uploading database backup: {e}")
    finally:
        # Удаляем локальные файлы
        os.remove(backup_path)
        os.remove(zip_file_path)

    # Удалить старые файлы резервных копий, если превышен лимит в 7
    try:
        # Получаем список файлов бэкапов
        files = s3.list_objects(Bucket=S3_BUCKET, Prefix=f"{db_name}/")["Contents"]
    except Exception as e:
        logger.debug(
            f"{e} The errors were caused by trying to connect to Selectel Cloud Storage"
        )
    # Сортируем по дате изменения
    sorted_files = sorted(files, key=lambda f: f["LastModified"], reverse=True)
    num_backups = len(sorted_files)
    logger.debug(f"Has {num_backups} backups")

    # Удаляем старые бэкапы, если их больше максимального лимита
    max_backups = 7
    if num_backups > max_backups:
        logger.debug(f"Deleting old backups")
        old_files = sorted_files[max_backups:]
        objects = [{"Key": f["Key"]} for f in old_files]
        s3.delete_objects(Bucket=S3_BUCKET, Delete={"Objects": objects})
