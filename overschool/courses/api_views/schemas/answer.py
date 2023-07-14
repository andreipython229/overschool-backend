from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class AnswersSchemas:
    def default_schema():
        return swagger_auto_schema(
            tags=["answers"],
        )

    def partial_update_schema():
        return swagger_auto_schema(
            tags=["answers"],
            manual_parameters=[
                openapi.Parameter(
                    name="body",
                    in_=openapi.IN_FORM,
                    description="HTML вариант ответа",
                    type=openapi.TYPE_STRING,
                    required=True,
                ),
                openapi.Parameter(
                    name="question",
                    in_=openapi.IN_FORM,
                    description="Вопрос, к которому привязан ответ",
                    type=openapi.TYPE_INTEGER,
                    required=True,
                ),
            ],
        )
