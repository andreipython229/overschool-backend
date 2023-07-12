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
