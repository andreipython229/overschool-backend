from datetime import datetime

from config.config import huey
from huey import crontab

from .pg_dump_config import db_config, run_pg_dump
from .upload_to_s3 import compress_and_upload_backup


@huey.periodic_task(
    crontab(hour=3, minute=0),
    max_retries=2,
    delay=None,
)
def backup_db():
    # Path for the backup file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Get the database name from the db_config dictionary
    db = list(db_config.keys())[0]

    # Run pg_dump command for the database
    backup_path = f"{db}_{timestamp}.backup"
    run_pg_dump(db, backup_path)

    # Perform compression and upload of the backup file
    compress_and_upload_backup(backup_path, db, 30)


@huey.periodic_task(
    crontab(minute=0, hour=1, day_of_week=2),
    max_retries=2,
    delay=None,
)
def weekly_backup():
    # Путь для файла резервной копии
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Получаем имя базы данных из словаря db_config
    db = list(db_config.keys())[0]

    # Запускаем команду pg_dump для базы данных
    backup_path = f"{db}_{timestamp}.backup"
    run_pg_dump(db, backup_path)

    # Выполняем сжатие и загрузку файла резервной копии
    compress_and_upload_backup(backup_path, f"weekly_{db}", 52)
