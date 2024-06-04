from ..models import TgUsers
from schools.models import School
from users.models import User
from ..models.completed_couses_notifications_log import CompletedCoursesNotificationsLog
from ..views import BotNotifications
from .notifications import CheckNotification


class CompletedCourseNotifications:
    """
        ТГ Уведомления для Админов о завершении учеником курса
    """

    @staticmethod
    def send_completed_course_notification(user_progress, user_id, course_id, course_name, school_id):

        if user_progress != 100:
            return
        else:
            try:

                # Проверяем, было ли уже отправлено уведомление для этого студента и курса

                if not CompletedCoursesNotificationsLog.objects.filter(user=user_id, course_id=course_id).exists():

                    # Получаем данные администратора школы и его Telegram id

                    school = School.objects.select_related('owner').get(school_id=school_id)
                    tg_admin_school = TgUsers.objects.get(user_id=school.owner.id)

                    # Проверка на уведомления

                    notifications = CheckNotification.notifications(tg_admin_school.id)
                    if notifications.get(tg_admin_school.id, {}).get('completed_courses', False):

                        # Получаем данные студента

                        student = User.objects.get(id=user_id)

                        # Отправляем уведомление

                        text = f"Ученик {student.last_name} {student.first_name} прошел курс {course_name}.\
                                Зайдите на платформу для дополнительной информации!"

                        BotNotifications.send_notifications(
                            tg_admin_school.tg_user_id,
                            text
                        )

                        # Записываем информацию о отправленном уведомлении в бд

                        CompletedCoursesNotificationsLog.objects.create(user_id=user_id, course_id=course_id)
            except:
                return
