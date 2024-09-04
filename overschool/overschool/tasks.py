import os

from common_services.selectel_client import UploadToS3
from huey.contrib.djhuey import task

s3 = UploadToS3()


@task()
def upload_video_task(temp_file_path, s3_file_path):
    # Получение размера файла
    file_size = os.path.getsize(temp_file_path)

    # Открытие файла и загрузка его на S3
    with open(temp_file_path, "rb") as file:
        s3.upload_large_file(file, s3_file_path, file_size=file_size)

    # Удаление временного файла
    os.remove(temp_file_path)
