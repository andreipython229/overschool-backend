from io import BytesIO

from common_services.selectel_client import UploadToS3
from huey.contrib.djhuey import task

s3 = UploadToS3()


@task()
def upload_video_task(video, file_path):
    video_stream = BytesIO(video.read())
    s3.upload_large_file(video_stream, file_path)
