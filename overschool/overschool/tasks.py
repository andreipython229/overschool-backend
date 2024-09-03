from common_services.selectel_client import UploadToS3
from huey.contrib.djhuey import db_task

s3 = UploadToS3()


@db_task()
def upload_video_task(video, file_path):
    file_path = s3.upload_large_file(video, file_path)
    return file_path
