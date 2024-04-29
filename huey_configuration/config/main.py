from backup.db_backup_task import backup_db, weekly_backup

from .config import huey

huey.periodic_task(backup_db, weekly_backup)

if __name__ == "__main__":
    huey.run()
