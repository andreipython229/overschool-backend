import subprocess

from config.config import (
    POSTGRES_DB_NAME,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USER,
    POSTGRES_USER_PASSWORD,
)
from loguru import logger

pg_dump_cmd_template = "pg_dump --dbname=postgresql://{user}:{password}@{host}:{port}/{database} -F c -b -v"

db_config = {
    "database": {
        "user": POSTGRES_USER,
        "password": POSTGRES_USER_PASSWORD,
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
        "database": POSTGRES_DB_NAME,
    },
}

logger.add("backup.log", rotation="10 MB", compression="zip")


def run_pg_dump(database, backup_path):
    try:
        pg_dump_cmd = pg_dump_cmd_template.format(**db_config[database])
        with open(backup_path, "wb") as backup_file:
            subprocess.run(pg_dump_cmd, stdout=backup_file, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        subprocess.run(["rm", backup_path])
        logger.error(f"Error backing up {database} database: {e}")
