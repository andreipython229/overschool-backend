from drf_yasg.utils import swagger_auto_schema

answer_schema = swagger_auto_schema(
    operation_description="""Эндпоинт на получение, создания, изменения и удаления ответов\n
    /api/{school_name}/answers/\n
    Разрешения для просмотра ответов к тестам (любой пользователь).\n
    Разрешения для создания и изменения ответов к тестам (только пользователи с группой 'Admin').""",
    operation_summary="Эндпоинт ответов",
    tags=["answers"],
    # responses={200: "Successful response"},
)
