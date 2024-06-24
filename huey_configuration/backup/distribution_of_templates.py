from huey import crontab
from config.config import huey
from config.db_utils import engine, school_table, newsletterTemplate_table, sentNewsletter_table
from sqlalchemy import select
from loguru import logger


@huey.periodic_task(crontab(minute='*'))
def distribution_of_templates():
    with engine.connect() as conn:
        school_query = select(school_table)
        newsletter_template_query = select(newsletterTemplate_table)
        sent_newsletter_query = select(sentNewsletter_table)
        school_query_result = conn.execute(school_query)
        newsletter_template_query_result = conn.execute(newsletter_template_query)
        sent_newsletter_query_result = conn.execute(sent_newsletter_query)

        for row in sent_newsletter_query_result.mappings():
            logger.info(f"School ID: {row['school_id']}, Name: {row['name']}, Created At: {row['created_at']}")

        logger.info(f"--------------------------------------------------------------------------------------------------------------------------------")

        for row in newsletter_template_query_result.mappings():
            logger.info(f"template name: {row['template_name']}, delay days: {row['delay_days']}, is public: {row['is_public']}")

        logger.info(
            f"--------------------------------------------------------------------------------------------------------------------------------")

        for row in school_query_result.mappings():
            logger.info(f"School ID: {row['school_id']}, Name: {row['name']}, Created At: {row['created_at']}")

        logger.info(
            f"--------------------------------------------------------------------------------------------------------------------------------")
