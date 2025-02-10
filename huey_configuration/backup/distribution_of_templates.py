from __future__ import annotations

import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.config import EMAIL_NAME, EMAIL_PASSWORD, huey
from config.db_utils import (
    engine,
    newsletterTemplate_table,
    school_table,
    sentNewsletter_table,
    users_table,
)
from huey import crontab
from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

TEMPLATES_DIR = "/templates/"


class SenderTemplateService:
    """
    Отправка на email шаблона для рассылки
    """

    def send_code_by_email(self, email: str, message: str, subject: str):
        msg = MIMEMultipart()
        msg["From"] = EMAIL_NAME
        msg["To"] = email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "html"))

        try:
            with smtplib.SMTP("smtp.yandex.com", 587) as server:
                server.starttls()
                server.login(EMAIL_NAME, EMAIL_PASSWORD)
                server.sendmail(EMAIL_NAME, email, msg.as_string())
        except Exception as e:
            logger.error(f"Error sending email to {email}: {e}")


sender_service = SenderTemplateService()


@huey.periodic_task(crontab(minute="0", hour="*/23"))
def distribution_of_templates():
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Получаем данные из таблиц
        school_query_result = session.execute(select(school_table)).mappings().all()
        newsletter_template_query_result = (
            session.execute(select(newsletterTemplate_table)).mappings().all()
        )
        sent_newsletter_query_result = (
            session.execute(select(sentNewsletter_table)).mappings().all()
        )
        users_query_result = session.execute(select(users_table)).mappings().all()

        # Преобразуем результаты в словари
        sent_newsletters = {
            (row["school_id"], row["template_id"]): row
            for row in sent_newsletter_query_result
        }
        users = {row["id"]: row for row in users_query_result}

        for school in school_query_result:
            school_id = school["school_id"]
            school_creation_date = school["created_at"]
            school_creation_date = school_creation_date.replace(tzinfo=None)
            creator_id = school["owner_id"]
            current_date = datetime.utcnow()

            for template in newsletter_template_query_result:
                template_name = template["template_name"]
                template_id = template["id"]
                template_text = template["text"]
                delay_days = template["delay_days"]
                is_public = template["is_public"]

                # Вычисляем дату для рассылки
                scheduled_date = school_creation_date + timedelta(days=delay_days)

                # Проверяем, пришло ли время для рассылки
                if is_public and current_date >= scheduled_date:
                    # Проверяем, не была ли уже выполнена рассылка этого шаблона для этой школы
                    if (school_id, template_id) not in sent_newsletters:
                        if creator_id in users:
                            email = users[creator_id]["email"]

                            subject = template_name

                            sender_service.send_code_by_email(
                                email=email, subject=subject, message=template_text
                            )

                            try:
                                session.execute(
                                    sentNewsletter_table.insert().values(
                                        school_id=school_id,
                                        template_id=template["id"],
                                        sent_at=current_date,
                                    )
                                )
                                session.commit()

                                # Обновляем словарь отправленных рассылок
                                sent_newsletters[(school_id, template_name)] = True

                            except SQLAlchemyError as e:
                                logger.error(
                                    f"Error inserting record into sent_newsletter_table: {e}"
                                )
                                session.rollback()

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        session.rollback()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        session.close()


@huey.periodic_task(crontab(minute="0", hour="7"))
def send_newsletter_emails():
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Получаем школы и их владельцев
        school_query_result = (
            session.execute(
                select(
                    school_table.c.school_id,
                    school_table.c.created_at,
                    school_table.c.owner_id,
                    users_table.c.email,
                ).join(users_table, school_table.c.owner_id == users_table.c.id)
            )
            .mappings()
            .all()
        )

        current_date = datetime.utcnow().date()

        # Кешируем шаблоны рассылки (загружаем один раз)
        templates_cache = {}
        for day in range(2, 31):  # Начинаем с дня 2
            template_path = os.path.join(TEMPLATES_DIR, f"{day}.html")
            if os.path.exists(template_path):
                with open(template_path, encoding="utf-8") as file:
                    templates_cache[day] = file.read()

        for school in school_query_result:
            email = school["email"]
            school_creation_date = school["created_at"].date()
            days_since_registration = (current_date - school_creation_date).days + 1

            # Проверяем, что день в диапазоне (от 2 до 30) и шаблон есть
            if (
                2 <= days_since_registration <= 30  # Начинаем с дня 2
                and days_since_registration in templates_cache
            ):
                email_content = templates_cache[days_since_registration]

                if email:
                    sender_service.send_code_by_email(
                        email,
                        email_content,
                        f"День {days_since_registration}: CourseHub",
                    )
            else:
                logger.warning(f"Нет шаблона для дня {days_since_registration}")

    except SQLAlchemyError as e:
        logger.error(f"Ошибка БД: {e}")
        session.rollback()
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
    finally:
        session.close()
