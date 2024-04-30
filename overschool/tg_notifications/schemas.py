from drf_yasg.utils import swagger_auto_schema

TAG = 'telegram notifications'


class TgNotificationsForStudent:

    @staticmethod
    def for_student_schema():
        return swagger_auto_schema(
            tags=[TAG],
            operation_description="Отправить уведомление Студенту",
            operation_summary="Отправить уведомление Студенту",
        )


class TgNotificationsForMentor:

    @staticmethod
    def for_mentor_schema():
        return swagger_auto_schema(
            tags=[TAG],
            operation_description="Отправить уведомление Ментору",
            operation_summary="Отправить уведомление Ментору",
        )