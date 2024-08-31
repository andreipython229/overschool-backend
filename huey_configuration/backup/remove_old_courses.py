from __future__ import annotations

import boto3
from huey import crontab
from config.config import (
    huey,
    ENDPOINT_URL,
    REGION_NAME,
    S3_ACCESS_KEY,
    S3_BUCKET,
    S3_SECRET_KEY,
)
from config.db_utils import (
    engine,
    course_table,
    course_landing_table,
    section_table,
    baselesson_table,
    baselessonblock_table,
    lesson_table,
    homework_table,
    userhomework_table,
    userhomeworkcheck_table,
    studentgroup_table,
    common_services_textfile_table,
    coursecopy_table,
    courses_sectiontest_table,
    courses_question_table,
    courses_answer_table,
    courses_usertest_table,
    courses_userprogresslogs_table,
    courses_blockbutton_table,
    common_services_audiofile_table,
    courses_groupcourseaccess_table,
    courses_studentsgroup_students_table,
    courses_studentshistory_table
)
from sqlalchemy import select, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from datetime import datetime, timedelta

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    region_name=REGION_NAME,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)


@huey.periodic_task(crontab(hour='*/23'))
def remove_old_courses():
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        current_date = datetime.utcnow()
        one_week_ago = current_date - timedelta(weeks=1)

        query = select(course_table).where(course_table.c.course_removed <= one_week_ago)
        courses_to_remove = session.execute(query).mappings().all()

        logger.info(f"Найдено {len(courses_to_remove)} курсов для удаления")

        for course in courses_to_remove:
            course_id = course['course_id']
            school_id = course['school_id']
            course_name = course['name']

            logger.info(f"Удаление курса ID: {course_id}, School ID: {school_id}, Name: {course_name}")

            try:
                section_ids = session.execute(
                    select(section_table.c.section_id).where(section_table.c.course_id == course_id)
                ).scalars().all()

                if section_ids:
                    baselessons_to_remove = session.execute(
                        select(baselesson_table.c.id).where(
                            baselesson_table.c.section_id.in_(section_ids)
                        )
                    ).scalars().all()

                    if baselessons_to_remove:
                        # Удаляем записи из таблицы lessons, которые ссылаются на baselessons
                        lessons_to_remove = session.execute(
                            select(lesson_table.c.lesson_id).where(
                                lesson_table.c.baselesson_ptr_id.in_(baselessons_to_remove)
                            )
                        ).scalars().all()

                        if lessons_to_remove:
                            session.execute(
                                delete(lesson_table).where(
                                    lesson_table.c.lesson_id.in_(lessons_to_remove)
                                )
                            )

                        # Удаление записей из homework и связанных таблиц
                        homework_ids_to_remove = session.execute(
                            select(homework_table.c.homework_id).where(
                                homework_table.c.baselesson_ptr_id.in_(baselessons_to_remove)
                            )
                        ).scalars().all()

                        if homework_ids_to_remove:
                            session.execute(
                                delete(homework_table).where(
                                    homework_table.c.homework_id.in_(homework_ids_to_remove)
                                )
                            )

                            user_homework_ids_to_remove = session.execute(
                                select(userhomework_table.c.user_homework_id).where(
                                    userhomework_table.c.homework_id.in_(homework_ids_to_remove)
                                )
                            ).scalars().all()

                            if user_homework_ids_to_remove:
                                user_homework_check_ids_to_remove = session.execute(
                                    select(userhomeworkcheck_table.c.user_homework_check_id).where(
                                        userhomeworkcheck_table.c.user_homework_id.in_(user_homework_ids_to_remove)
                                    )
                                ).scalars().all()

                                if user_homework_check_ids_to_remove:
                                    session.execute(
                                        delete(common_services_textfile_table).where(
                                            common_services_textfile_table.c.user_homework_check_id.in_(
                                                user_homework_check_ids_to_remove
                                            )
                                        )
                                    )

                                session.execute(
                                    delete(userhomeworkcheck_table).where(
                                        userhomeworkcheck_table.c.user_homework_id.in_(user_homework_ids_to_remove)
                                    )
                                )

                            session.execute(
                                delete(userhomework_table).where(
                                    userhomework_table.c.user_homework_id.in_(user_homework_ids_to_remove)
                                )
                            )

                        # Удаление тестов и связанных данных
                        test_ids_to_remove = session.execute(
                            select(courses_sectiontest_table.c.test_id).where(
                                courses_sectiontest_table.c.baselesson_ptr_id.in_(baselessons_to_remove)
                            )
                        ).scalars().all()

                        if test_ids_to_remove:
                            session.execute(
                                delete(courses_usertest_table).where(
                                    courses_usertest_table.c.test_id.in_(test_ids_to_remove)
                                )
                            )

                            question_ids_to_remove = session.execute(
                                select(courses_question_table.c.question_id).where(
                                    courses_question_table.c.test_id.in_(test_ids_to_remove)
                                )
                            ).scalars().all()

                            if question_ids_to_remove:
                                session.execute(
                                    delete(courses_answer_table).where(
                                        courses_answer_table.c.question_id.in_(question_ids_to_remove)
                                    )
                                )

                                session.execute(
                                    delete(courses_question_table).where(
                                        courses_question_table.c.question_id.in_(question_ids_to_remove)
                                    )
                                )

                            session.execute(
                                delete(courses_sectiontest_table).where(
                                    courses_sectiontest_table.c.test_id.in_(test_ids_to_remove)
                                )
                            )

                        # Удаление блоков и связанных данных
                        block_ids_to_remove = session.execute(
                            select(baselessonblock_table.c.id).where(
                                baselessonblock_table.c.base_lesson_id.in_(baselessons_to_remove)
                            )
                        ).scalars().all()

                        if block_ids_to_remove:
                            session.execute(
                                delete(courses_blockbutton_table).where(
                                    courses_blockbutton_table.c.block_id.in_(block_ids_to_remove)
                                )
                            )

                        session.execute(
                            delete(baselessonblock_table).where(
                                baselessonblock_table.c.base_lesson_id.in_(baselessons_to_remove)
                            )
                        )

                        # Удаление других связанных данных
                        session.execute(
                            delete(courses_userprogresslogs_table).where(
                                courses_userprogresslogs_table.c.lesson_id.in_(baselessons_to_remove)
                            )
                        )

                        session.execute(
                            delete(common_services_audiofile_table).where(
                                common_services_audiofile_table.c.base_lesson_id.in_(baselessons_to_remove)
                            )
                        )

                        session.execute(
                            delete(baselesson_table).where(
                                baselesson_table.c.id.in_(baselessons_to_remove)
                            )
                        )

                    # Удаляем записи из section
                    session.execute(
                        delete(section_table).where(
                            section_table.c.section_id.in_(section_ids)
                        )
                    )

                    group_ids_to_remove = session.execute(
                        select(studentgroup_table.c.group_id).where(
                            studentgroup_table.c.course_id_id == course_id
                        )
                    ).scalars().all()

                    if group_ids_to_remove:
                        session.execute(
                            delete(courses_studentshistory_table).where(
                                courses_studentshistory_table.c.students_group_id.in_(group_ids_to_remove)
                            )
                        )

                        session.execute(
                            delete(courses_studentsgroup_students_table).where(
                                courses_studentsgroup_students_table.c.studentsgroup_id.in_(group_ids_to_remove)
                            )
                        )

                        session.execute(
                            delete(courses_groupcourseaccess_table).where(
                                courses_groupcourseaccess_table.c.group_id.in_(group_ids_to_remove)
                            )
                        )

                    session.execute(
                        delete(studentgroup_table).where(
                            studentgroup_table.c.course_id_id == course_id
                        )
                    )

                session.execute(
                    delete(course_landing_table).where(
                        course_landing_table.c.course_id == course_id
                    )
                )

                # Удаление файлов из S3
                s3_prefix = f"{school_id}_school/{course_id}_course"
                files_to_delete = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=s3_prefix).get('Contents', [])
                if files_to_delete:
                    delete_objects = [{'Key': file['Key']} for file in files_to_delete]
                    s3.delete_objects(Bucket=S3_BUCKET, Delete={'Objects': delete_objects})
                    logger.info(f"Удалены файлы из S3 для курса ID {course_id}")
                else:
                    logger.info(f"Файлы для курса ID {course_id} не найдены в S3")

                session.execute(
                    delete(coursecopy_table).where(
                        coursecopy_table.c.course_id == course_id
                    )
                )
                session.execute(
                    delete(course_table).where(
                        course_table.c.course_id == course_id
                    )
                )
                logger.info(f"Удаляемый ориг курс - {course_id}")

            except Exception as e:
                logger.error(f"Ошибка при удалении курса: {e}")
                session.rollback()

            try:
                # Проверка и удаление копий курса
                copy_query = select(course_table).where(
                    course_table.c.name == course_name,
                    course_table.c.is_copy == True
                )
                copies_to_remove = session.execute(copy_query).mappings().all()

                for copy_course in copies_to_remove:
                    copy_course_id = copy_course['course_id']

                    copy_section_ids = session.execute(
                        select(section_table.c.section_id).where(section_table.c.course_id == copy_course_id)
                    ).scalars().all()

                    if copy_section_ids:
                        # Удаление уроков, связанных с копиями
                        session.execute(
                            delete(lesson_table).where(
                                lesson_table.c.baselesson_ptr_id.in_(copy_section_ids)
                            )
                        )

                        # Удаление групп и связанных данных для копий курса
                        group_ids_to_remove = session.execute(
                            select(studentgroup_table.c.group_id).where(
                                studentgroup_table.c.course_id_id == copy_course_id
                            )
                        ).scalars().all()

                        if group_ids_to_remove:
                            session.execute(
                                delete(courses_studentshistory_table).where(
                                    courses_studentshistory_table.c.students_group_id.in_(group_ids_to_remove)
                                )
                            )

                            session.execute(
                                delete(courses_studentsgroup_students_table).where(
                                    courses_studentsgroup_students_table.c.studentsgroup_id.in_(group_ids_to_remove)
                                )
                            )

                            session.execute(
                                delete(courses_groupcourseaccess_table).where(
                                    courses_groupcourseaccess_table.c.group_id.in_(group_ids_to_remove)
                                )
                            )

                        session.execute(
                            delete(section_table).where(
                                section_table.c.section_id.in_(copy_section_ids)
                            )
                        )
                        session.execute(
                            delete(studentgroup_table).where(
                                studentgroup_table.c.course_id_id == copy_course_id
                            )
                        )

                    session.execute(
                        delete(course_table).where(
                            course_table.c.course_id == copy_course_id
                        )
                    )

                session.commit()

            except Exception as e:
                logger.error(f"Ошибка при удалении копий курса {course_name}: {e}")
                session.rollback()

        session.commit()
        logger.info(f"Успешно удалены {len(courses_to_remove)} старых курсов и их копий.")

    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных: {e}")
        session.rollback()
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
    finally:
        session.close()
