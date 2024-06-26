from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from huey import crontab
from config.config import huey, EMAIL_NAME, EMAIL_PASSWORD
from config.db_utils import engine, school_table, newsletterTemplate_table, sentNewsletter_table, users_table
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from datetime import datetime, timedelta


class SenderTemplateService:
    """
    Отправка на email шаблона для рассылки
    """

    def send_code_by_email(self, email: str, message: str, subject: str):
        msg = MIMEMultipart()
        msg['From'] = EMAIL_NAME
        msg['To'] = email
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'html'))

        try:
            with smtplib.SMTP('smtp.yandex.com', 587) as server:
                server.starttls()
                server.login(EMAIL_NAME, EMAIL_PASSWORD)
                server.sendmail(EMAIL_NAME, email, msg.as_string())
        except Exception as e:
            logger.error(f"Error sending email to {email}: {e}")


sender_service = SenderTemplateService()


@huey.periodic_task(crontab(minute='0', hour='*/23'))
def distribution_of_templates():
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Получаем данные из таблиц
        school_query_result = session.execute(select(school_table)).mappings().all()
        newsletter_template_query_result = session.execute(select(newsletterTemplate_table)).mappings().all()
        sent_newsletter_query_result = session.execute(select(sentNewsletter_table)).mappings().all()
        users_query_result = session.execute(select(users_table)).mappings().all()

        # Преобразуем результаты в словари
        sent_newsletters = {(row['school_id'], row['template_id']): row for row in sent_newsletter_query_result}
        users = {row['id']: row for row in users_query_result}

        for school in school_query_result:
            school_id = school['school_id']
            school_creation_date = school['created_at']
            school_creation_date = school_creation_date.replace(tzinfo=None)
            creator_id = school['owner_id']
            current_date = datetime.utcnow()

            for template in newsletter_template_query_result:
                template_name = template['template_name']
                template_id = template['id']
                template_text = template['text']
                delay_days = template['delay_days']
                is_public = template['is_public']

                # Вычисляем дату для рассылки
                scheduled_date = school_creation_date + timedelta(days=delay_days)

                # Проверяем, пришло ли время для рассылки
                if is_public and current_date >= scheduled_date:
                    # Проверяем, не была ли уже выполнена рассылка этого шаблона для этой школы
                    if (school_id, template_id) not in sent_newsletters:
                        if creator_id in users:
                            email = users[creator_id]['email']

                            subject = template_name

                            sender_service.send_code_by_email(
                                email=email,
                                subject=subject,
                                message=template_text
                            )

                            try:
                                session.execute(
                                    sentNewsletter_table.insert().values(
                                        school_id=school_id,
                                        template_id=template['id'],
                                        sent_at=current_date
                                    )
                                )
                                session.commit()

                                # Обновляем словарь отправленных рассылок
                                sent_newsletters[(school_id, template_name)] = True

                            except SQLAlchemyError as e:
                                logger.error(f"Error inserting record into sent_newsletter_table: {e}")
                                session.rollback()

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        session.rollback()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        session.close()
