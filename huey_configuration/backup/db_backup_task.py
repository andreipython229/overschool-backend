from datetime import datetime

from config.config import huey
from huey import crontab

from .pg_dump_config import db_config, run_pg_dump
from .upload_to_s3 import compress_and_upload


# The task starts every day at 1:00.
# @huey.periodic_task(
#     crontab(hour=1, minute=0),
#     max_retries=3,
#     delay=7200,
# )
@huey.periodic_task(
    crontab(hour="*", minute=0),
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
    zip_file_path = f"{db}_{timestamp}.zip"
    compress_and_upload(backup_path, zip_file_path, db)
