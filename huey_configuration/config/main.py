from backup.db_backup_task import backup_db, weekly_backup
from backup.distribution_of_templates import distribution_of_templates
from backup.meetings_reminders import meeting_reminders_tg

from .config import huey
from .db_utils import engine, meta

if __name__ == "__main__":
    # Подключаемся к базе данных при запуске
    with engine.connect() as conn:
        meta.reflect(bind=engine)

    huey.periodic_task(backup_db, weekly_backup)
    huey.periodic_task(distribution_of_templates)
    huey.periodic_task(meeting_reminders_tg)

    huey.run()
