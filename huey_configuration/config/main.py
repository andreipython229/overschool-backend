from backup.db_backup_task import backup_db

from .config import huey

huey.periodic_task(backup_db)

if __name__ == "__main__":
    huey.run()
