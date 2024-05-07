import os
import telebot
from time import gmtime
from .models import TgUsers, Notifications
from schools.models import School
from users.models import User

bot_token = os.environ.get('TG_BOT_TOKEN')
bot = telebot.TeleBot(bot_token)


class SendNotifications:

    _last_notifications = {}
    _last_complited_course_notifications = {}

    @staticmethod
    def last_notifications(user_homework, last_check_status, last_check_mark):

        """
            Функция для обработки дубликатов при создании домашек
        """

        duplicate = {last_check_status: gmtime()}
        if duplicate in SendNotifications._last_notifications.values():
            return
        else:
            print("отпрвляется сообщение", duplicate, SendNotifications._last_notifications.values())
            SendNotifications.send_telegram_notification(user_homework, last_check_status, last_check_mark)

    @staticmethod
    def send_telegram_notification(user_homework, last_check_status, last_check_mark):
        if last_check_status == 'Ждет проверки':
            try:
                query = TgUsers.objects.filter(user_id=user_homework.teacher_id)

                mentor = {
                    mentor.user_id: {
                        'tg_user_id': mentor.tg_user_id,
                        'first_name': mentor.first_name
                    } for mentor in query
                }

                mentor_chat_id = mentor[user_homework.teacher_id]['tg_user_id']

                bot.send_message(
                    chat_id=mentor_chat_id,
                    text='Ученик прислал работу на проверку! Не забудьте проверить работу ученика на платформе!'
                )
                print('сообщение отправлено ментору')

                SendNotifications._last_notifications[last_check_status] = {
                    last_check_status: gmtime()
                }
            except Exception as e:
                return f"{e}"
        else:
            try:
                query = TgUsers.objects.filter(user_id=user_homework.user_id)

                student = {
                    student.user_id: {
                        'tg_user_id': student.tg_user_id,
                        'first_name': student.first_name
                    } for student in query
                }

                student_chat_id = student[user_homework.user_id]['tg_user_id']

                bot.send_message(
                    chat_id=student_chat_id,
                    text=f"Ментор проверил ваше задание. Зайдите на платформу для дополнительной информации!"
                )
                print('сообщение отправлено студенту')

                # SendNotifications._last_notifications[last_check_status] = {
                #     last_check_status: gmtime()
                # }
            except Exception as e:
                return f"{e}"

    @staticmethod
    def last_complited_course_notifications(user_progress, student, course_id, course_name, school_id):

        """
            Функция для обработки дубликатов
        """

        duplicate = {student.pk: course_id}
        if duplicate in SendNotifications._last_complited_course_notifications.values():
            return
        else:
            print("отпрвляется сообщение", duplicate, SendNotifications._last_complited_course_notifications.values())
            SendNotifications.send_complited_course_notification(user_progress, student, course_id, course_name, school_id)

    @staticmethod
    def send_complited_course_notification(user_progress, student, course_id, course_name, school_id):

        if user_progress != 100:
            return
        else:
            try:
                # уведомление для АДМИНА школы
                school = School.objects.get(school_id=school_id)
                admin_school = User.objects.get(id=school.owner_id).id

                tg_admin_school = TgUsers.objects.get(user_id=admin_school).tg_user_id
                bot.send_message(
                    chat_id=tg_admin_school,
                    text=f"Ученик {student.last_name} {student.first_name} прошел курс {course_name}. Зайдите на платформу для дополнительной информации!"
                )

                SendNotifications._last_complited_course_notifications[student.pk] = {
                    student.pk: course_id
                }
            except:
                print('Админ школы не подключил тг уведомления!')

            # try:
            #     # уведомление для МЕНТОРА курса
            #
            #     mentor = StudentsGroup.objects.get(course_id_id=course_id).teacher_id_id
            #
            #     tg_mentor_course = TgUsers.objects.get(user_id=mentor).tg_user_id
            #     bot.send_message(
            #         chat_id=tg_mentor_course,
            #         text=f"Ученик {student.last_name} {student.first_name} прошел курс {course_name}. Зайдите на платформу для дополнительной информации!"
            #     )
            #
                # SendNotifications._last_complited_course_notifications[student.pk] = {
                #     student.pk: course_id
                # }
            # except:
            #     print('Ментор курса не подключил тг уведомления!')