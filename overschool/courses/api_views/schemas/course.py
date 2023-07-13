from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

course_schema = swagger_auto_schema(
    operation_description="""Эндпоинт для просмотра, создания, изменения и удаления курсов \n
        /api/{school_name}/courses/\n
        Получать курсы может любой пользователь.\n
        Создавать, изменять, удалять - пользователь с правами группы Admin.""",
    operation_summary="Эндпоинт курсов",
    tags=["courses"],
    # responses={200: "Successful response"},
)


class CoursesSchemas:
    def courses_create_schema():
        return swagger_auto_schema(
            tags=["courses"],
        )

    def courses_update_schema():
        return swagger_auto_schema(
            tags=["courses"],
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
