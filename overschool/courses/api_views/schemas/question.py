from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class QuestionsSchemas:
    def default_schema():
        return swagger_auto_schema(
            operation_description="""Эндпоинт на получение, создания, изменения и удаления вопросов\n
            /api/{school_name}/questions/\n
            Получать вопросы может любой пользователь. \n
            Создавать, изменять, удалять - пользователь с правами группы Admin.""",
            operation_summary="Эндпоинт на получение, создания, изменения и удаления вопросов",
            tags=["questions"],
            # responses={200: "Successful response"},
        )

    def question_update_schema():
        return swagger_auto_schema(
            tags=["questions"],
            manual_parameters=[
                openapi.Parameter(
                    name="body",
                    in_=openapi.IN_FORM,
                    description="body",
                    type=openapi.TYPE_STRING,
                    required=False,
                )
            ],
        )
