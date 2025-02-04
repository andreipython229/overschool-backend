import io
import os
import zipfile
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from overschool.settings import (
    ENDPOINT_URL,
    REGION_NAME,
    S3_ACCESS_KEY,
    S3_BUCKET,
    S3_SECRET_KEY,
)


class UploadToS3:
    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION_NAME,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    )
    ALLOWED_FORMATS = [
        ".xlsx",
        ".pdf",
        ".csv",
        ".txt",
        ".doc",
        ".docx",
        ".json",
        ".rtf",
        ".xml",
        ".yaml",
        ".jpg",
        ".jpeg",
        ".png",
    ]

    def get_link(self, filename):
        url = self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": filename},
            ExpiresIn=14400,
        )
        return url

    def delete_file(self, filename):
        self.s3.delete_object(Bucket=S3_BUCKET, Key=filename)

    def delete_files(self, objects_to_delete):
        self.s3.delete_objects(Bucket=S3_BUCKET, Delete={"Objects": objects_to_delete})

    def get_list_objects(self, prefix):
        response = self.s3.list_objects(Bucket=S3_BUCKET, Prefix=f"{prefix}")
        if "Contents" in response:
            items = response["Contents"]
            objects_to_delete = [{"Key": item["Key"]} for item in items]
            return objects_to_delete
        else:
            return None

    def get_size_object(self, key):
        try:
            response = self.s3.head_object(Bucket=S3_BUCKET, Key=key)
            if "ContentLength" in response:
                return response["ContentLength"]
            else:
                return None
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return None
            else:
                raise

    def upload_course_image(self, uploaded_image, course):
        course_id = course.course_id
        school_id = course.school.school_id
        file_path = "{}_school/{}_course/{}@{}".format(
            school_id,
            course_id,
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f"),
            uploaded_image.name,
        ).replace(" ", "_")
        self.s3.upload_fileobj(uploaded_image, S3_BUCKET, file_path)
        return file_path

    def upload_course_landing_images(self, uploaded_image, course):
        course_id = course.course_id
        school_id = course.school.school_id
        file_path = "{}_school/{}_course/landing/{}@{}".format(
            school_id,
            course_id,
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f"),
            uploaded_image.name,
        ).replace(" ", "_")
        self.s3.upload_fileobj(uploaded_image, S3_BUCKET, file_path)
        return file_path

    def upload_school_image(self, uploaded_image, school_id):
        file_path = "{}_school/school_data/images/{}@{}".format(
            school_id,
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f"),
            uploaded_image.name,
        ).replace(" ", "_")
        self.s3.upload_fileobj(uploaded_image, S3_BUCKET, file_path)
        return file_path

    def upload_avatar(self, avatar, user_id):
        file_path = "users/avatars/{}@{}".format(user_id, avatar.name).replace(" ", "_")
        self.s3.upload_fileobj(avatar, S3_BUCKET, file_path)
        return file_path

    def upload_avatar_feedback(self, avatar, feedback_id):
        file_path = "users/avatars/feedback/{}@{}".format(
            feedback_id, avatar.name
        ).replace(" ", "_")
        self.s3.upload_fileobj(avatar, S3_BUCKET, file_path)
        return file_path

    def upload_file_chat(self, file, chat):
        file_path = "chats/files/{}@{}".format(chat, file.name).replace(" ", "_")
        self.s3.upload_fileobj(file, S3_BUCKET, file_path)
        return file_path

    def upload_file(self, filename, base_lesson):
        course = base_lesson.section.course
        course_id = course.course_id
        school_id = course.school.school_id
        name, ext = os.path.splitext(filename.name)
        ext = ext.lower()
        if ext not in self.ALLOWED_FORMATS:
            zip_data = self.get_zip_file(filename)
            file_path = (
                "{}_school/{}_course/{}_lesson/{}@{}".format(
                    school_id,
                    course_id,
                    base_lesson.id,
                    datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f"),
                    name,
                ).replace(" ", "_")
                + ".zip"
            )
            self.s3.upload_fileobj(io.BytesIO(zip_data), S3_BUCKET, file_path)
        else:
            file_path = "{}_school/{}_course/{}_lesson/{}@{}".format(
                school_id,
                course_id,
                base_lesson.id,
                datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f"),
                filename,
            ).replace(" ", "_")
            self.s3.upload_fileobj(filename, S3_BUCKET, file_path)
        return file_path

    def file_path(self, filename, base_lesson):
        course = base_lesson.section.course
        course_id = course.course_id
        school_id = course.school.school_id
        file_path = "{}_school/{}_course/{}_lesson/{}@{}".format(
            school_id,
            course_id,
            base_lesson.id,
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f"),
            filename,
        ).replace(" ", "_")
        return file_path

    def upload_large_file(self, filename, base_lesson):
        course = base_lesson.section.course
        course_id = course.course_id
        school_id = course.school.school_id
        file_path = "{}_school/{}_course/{}_lesson/{}@{}".format(
            school_id,
            course_id,
            base_lesson.id,
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f"),
            filename,
        ).replace(" ", "_")

        # Определите размер файла
        segment_size = 50 * 1024 * 1024
        file_size = filename.size

        if file_size <= segment_size:
            self.s3.upload_fileobj(filename, S3_BUCKET, file_path)
            return file_path

        # Создаем загрузочный объект
        multipart_upload = self.s3.create_multipart_upload(
            Bucket=S3_BUCKET,
            Key=file_path,
        )
        upload_id = multipart_upload["UploadId"]
        part_number = 1
        offset = 0
        parts = []  # Список для хранения информации о частях

        try:
            while offset < file_size:
                # Читаем сегмент файла
                data = filename.read(segment_size)

                # Загружаем сегмент
                response = self.s3.upload_part(
                    Body=data,
                    Bucket=S3_BUCKET,
                    Key=file_path,
                    PartNumber=part_number,
                    UploadId=upload_id,
                )

                # Сохраняем информацию о части
                parts.append({"ETag": response["ETag"], "PartNumber": part_number})
                part_number += 1
                offset += len(data)

            # Завершаем многозадачную загрузку, предоставляя информацию о частях
            self.s3.complete_multipart_upload(
                Bucket=S3_BUCKET,
                Key=file_path,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )

            return file_path
        except Exception as e:
            # Произошла ошибка, нужно отменить многозадачную загрузку
            self.s3.abort_multipart_upload(
                Bucket=S3_BUCKET, Key=file_path, UploadId=upload_id
            )
            raise e

    def get_zip_file(self, file):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(file.name, file.read())
        return zip_buffer.getvalue()
