from __future__ import annotations

import os

from huey import crontab
from config.config import huey, EMAIL_NAME, EMAIL_PASSWORD
from config.db_utils import engine, meeting_reminder_table, association_table, users_table, school_meetings_table, \
    tgusers_table, students_table
from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from datetime import timedelta
import telebot
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()


def send_reminders(chat_id, message):
    bot = telebot.TeleBot(os.getenv('API_TOKEN'))
    bot.send_message(
        chat_id,
        message
    )


@huey.periodic_task(crontab(minute='*/1'))
def meeting_reminders_tg():
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        reminders = session.execute(select(
            meeting_reminder_table
        ).filter(
            meeting_reminder_table.c.meeting_id == association_table.c.schoolmeetings_id  # type: ignore
        ).where(
            meeting_reminder_table.c.sent == False
        )).mappings().all()

        logger.debug(f'Reminder:{reminders}')

        for reminder in reminders:
            meeting_id = reminder['meeting_id']

            students = session.execute(
                select(
                    students_table.c.user_id
                ).filter(
                    association_table.c.schoolmeetings_id == meeting_id,  # type: ignore
                    association_table.c.studentsgroup_id == students_table.c.studentsgroup_id  # type: ignore
                )
            ).mappings().all()

            rem_daily = reminder['daily']
            rem_in_three_hours = reminder['in_three_hours']
            rem_in_ten_minute = reminder['ten_minute']

            for student in students:

                user = student['user_id']

                tg_user_chat_id = session.execute(
                    select(tgusers_table.c.tg_user_id)
                    .where(
                        tgusers_table.c.user_id == user  # type: ignore
                    )
                ).mappings().all()

                start_date_query = session.execute(
                    select(
                        school_meetings_table.c.start_date
                    ).where(
                        school_meetings_table.c.id == meeting_id  # type: ignore
                    )
                ).mappings().all()

                start_date = start_date_query[0]['start_date']

                # За день

                if rem_daily is True and datetime.now(timezone.utc) >= start_date - timedelta(days=1):
                    message = f'НАПОМИНАНИЕ! У вас на завтра назначена видеоконференция! \
                                            Для дополнительной информации перейдите на платформу overschool.by'
                    send_reminders(tg_user_chat_id[0]["tg_user_id"], message)

                    session.execute(update(meeting_reminder_table).where(
                        meeting_reminder_table.c.meeting_id == meeting_id  # type: ignore
                    ).values(daily=False))
                    session.commit()

                # За 3 часа

                if rem_in_three_hours is True and datetime.now(timezone.utc) >= start_date - timedelta(hours=3):
                    message = f'НАПОМИНАНИЕ! До начала видеокнференции осталось 3 часа!'
                    send_reminders(tg_user_chat_id[0]["tg_user_id"], message)

                    session.execute(update(meeting_reminder_table).where(
                        meeting_reminder_table.c.meeting_id == meeting_id  # type: ignore
                    ).values(in_three_hours=False))
                    session.commit()

                # За 10 минут

                if rem_in_ten_minute is True and datetime.now(timezone.utc) >= start_date - timedelta(minutes=10):
                    message = f'НАПОМИНАНИЕ! Видеоконферения начнется через 10 минут!'
                    send_reminders(tg_user_chat_id[0]["tg_user_id"], message)

                    session.execute(update(meeting_reminder_table).where(
                        meeting_reminder_table.c.meeting_id == meeting_id  # type: ignore
                    ).values(ten_minute=False))
                    session.commit()

                # Перед началом Видеоконференции

                if datetime.now(timezone.utc) >= start_date:
                    message = f'Видеоконференция уже началась! Перейдите на платформу overschool.by, чтобы стать участником!'
                    send_reminders(tg_user_chat_id[0]["tg_user_id"], message)

                    session.execute(update(meeting_reminder_table).where(
                        meeting_reminder_table.c.meeting_id == meeting_id  # type: ignore
                    ).values(sent=True))
                    session.commit()

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        session.rollback()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        session.close()
