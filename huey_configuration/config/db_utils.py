import os
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, Table, Column, Integer, String, inspect, ForeignKey
from sqlalchemy.orm import sessionmaker
from loguru import logger

load_dotenv()

engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_USER_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB_NAME')}",
    echo=True
)

Session = sessionmaker(bind=engine)
session = Session()

meta = MetaData()
meta.bind = engine

school_table = Table('schools_school', meta, autoload_with=engine)
newsletterTemplate_table = Table('schools_newslettertemplate', meta, autoload_with=engine)
sentNewsletter_table = Table('schools_sentnewsletter', meta, autoload_with=engine)
users_table = Table('users_user', meta, autoload_with=engine)
course_table = Table('courses_course', meta, autoload_with=engine)
course_landing_table = Table('courses_courselanding', meta, autoload_with=engine)
section_table = Table('courses_section', meta, autoload_with=engine)
baselesson_table = Table('courses_baselesson', meta, autoload_with=engine)
baselessonblock_table = Table('courses_baselessonblock', meta, autoload_with=engine)
lesson_table = Table('courses_lesson', meta, autoload_with=engine)
homework_table = Table('courses_homework', meta, autoload_with=engine)
userhomework_table = Table('courses_userhomework', meta, autoload_with=engine)
studentgroup_table = Table('courses_studentsgroup', meta, autoload_with=engine)
userhomeworkcheck_table = Table('courses_userhomeworkcheck', meta, autoload_with=engine)
common_services_textfile_table = Table('common_services_textfile', meta, autoload_with=engine)
coursecopy_table = Table('courses_coursecopy', meta, autoload_with=engine)
courses_sectiontest_table = Table('courses_sectiontest', meta, autoload_with=engine)
courses_question_table = Table('courses_question', meta, autoload_with=engine)
courses_answer_table = Table('courses_answer', meta, autoload_with=engine)
courses_usertest_table = Table('courses_usertest', meta, autoload_with=engine)
courses_userprogresslogs_table = Table('courses_userprogresslogs', meta, autoload_with=engine)
courses_blockbutton_table = Table('courses_blockbutton', meta, autoload_with=engine)
common_services_audiofile_table = Table('common_services_audiofile', meta, autoload_with=engine)
courses_groupcourseaccess_table = Table('courses_groupcourseaccess', meta, autoload_with=engine)
courses_studentsgroup_students_table = Table('courses_studentsgroup_students', meta, autoload_with=engine)
courses_studentshistory_table = Table('courses_studentshistory', meta, autoload_with=engine)

tgusers_table = Table('tg_notifications_tgusers', meta, autoload_with=engine)
meeting_reminder_table = Table('tg_notifications_meetingsreminderstg', meta, autoload_with=engine)
school_meetings_table = Table('schools_schoolmeetings', meta, autoload_with=engine)
students_table = Table('courses_studentsgroup_students', meta, autoload_with=engine)
association_table = Table(
    'schools_schoolmeetings_students_groups', meta,
    Column('schoolmeetings_id', Integer, ForeignKey('schools_schoolmeetings.id')),
    Column('studentsgroup_id', Integer, ForeignKey('courses_studentsgroup.group_id'), autoload_with=engine)
)
