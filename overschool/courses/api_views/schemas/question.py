from drf_yasg.utils import swagger_auto_schema

question_schema = swagger_auto_schema(
    operation_description="""Эндпоинт на получение, создания, изменения и удаления вопросов\n
    /api/{school_name}/questions/\n
    Получать вопросы может любой пользователь. \n
    Создавать, изменять, удалять - пользователь с правами группы Admin.""",
    operation_summary="Эндпоинт вопросов",
    tags=["questions"],
    # responses={200: "Successful response"},
)
