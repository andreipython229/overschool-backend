from drf_yasg.utils import swagger_auto_schema

lesson_schema = swagger_auto_schema(
    operation_description="""Эндпоинт на получение, создания, изменения и удаления уроков\n
    /api/{school_name}/lessons/\n
    Разрешения для просмотра уроков (любой пользователь)\n
    Разрешения для создания и изменения уроков (только пользователи с группой 'Admin')""",
    operation_summary="Эндпоинт уроков",
    tags=["lessons"],
    # responses={200: "Successful response"},
)
