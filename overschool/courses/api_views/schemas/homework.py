from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

homework_schema = swagger_auto_schema(
    operation_description="""Эндпоинт на получение, создания, изменения и удаления домашних заданий.\n
        /api/{school_name}/homeworks/\n
        Разрешения для просмотра домашних заданий (любой пользователь).\n\n
        Разрешения для создания и изменения домашних заданий (только пользователи с группой 'Admin').""",
    operation_summary="Эндпоинт домашек",
    tags=["homeworks"],
    # responses={200: "Successful response"},
)


class HomeworkSchemas:
    def homework_get_and_create_schema():
        return swagger_auto_schema(
            tags=["homeworks"],
        )

    def homework_update_schema():
        return swagger_auto_schema(
            tags=["homeworks"],
            manual_parameters=[
                openapi.Parameter(
                    name="order",
                    in_=openapi.IN_FORM,
                    description="order",
                    type=openapi.TYPE_INTEGER,
                    required=False,
                ),
                openapi.Parameter(
                    name="school",
                    in_=openapi.IN_FORM,
                    description="school",
                    type=openapi.TYPE_INTEGER,
                    required=False,
                ),
                openapi.Parameter(
                    name="sections",
                    in_=openapi.IN_FORM,
                    description="sections",
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type="integer"),
                    required=False,
                ),
                openapi.Parameter(
                    name="course_id",
                    in_=openapi.IN_FORM,
                    description="course_id",
                    type=openapi.TYPE_INTEGER,
                    required=True,
                ),
            ],
        )
