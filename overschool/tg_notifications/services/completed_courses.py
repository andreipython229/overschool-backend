from ..models import TgUsers, Notifications
from schools.models import School
from users.models import User
from ..views import bot, CheckNotification


class CompletedCourseNotifications:

    _last_complited_course_notifications = {}

    @staticmethod
    def last_complited_course_notifications(user_progress, student, course_id, course_name, school_id):
        """
            Функция для обработки дубликатов
        """

        duplicate = {student.pk: course_id}
        if duplicate in CompletedCourseNotifications._last_complited_course_notifications.values():
            return
        else:
            CompletedCourseNotifications.send_complited_course_notification(user_progress, student, course_id, course_name, school_id)

    @staticmethod
    def send_complited_course_notification(user_progress, student, course_id, course_name, school_id):
        if user_progress != 100:
            return
        else:
            try:

                # уведомление для АДМИНА школы
                school = School.objects.get(school_id=school_id)
                admin_school = User.objects.get(id=school.owner_id).id
                tg_admin = TgUsers.objects.get(user_id=admin_school)

                # проверка на уведомления

                notifications = CheckNotification.notifications(tg_admin.id)
                if notifications[tg_admin.id]['comleted_courses'] is True:

                    bot.send_message(
                        chat_id=tg_admin.tg_user_id,
                        text=f"Ученик {student.last_name} {student.first_name} прошел курс {course_name}. Зайдите на платформу для дополнительной информации!"
                    )

                    CompletedCourseNotifications._last_complited_course_notifications[student.pk] = {
                        student.pk: course_id
                    }
                    print('Уведомление отправлено!')
                else:
                    print('Админ не включил уведомления о завершении курса!')
            except:
                print('Админ школы не подключил тг уведомления!')
