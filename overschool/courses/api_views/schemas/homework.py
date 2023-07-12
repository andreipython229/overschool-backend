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
