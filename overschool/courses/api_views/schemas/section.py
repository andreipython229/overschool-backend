from drf_yasg.utils import swagger_auto_schema

section_schema = swagger_auto_schema(
    operation_description="""Эндпоинт получения, создания, редактирования и удаления секций.\n
        /api/{school_name}/sections/\n
        Разрешения для просмотра секций (любой пользователь)\n
        Разрешения для создания и изменения секций (только пользователи с группой 'Admin')""",
    operation_summary="Эндпоинт секций",
    tags=["sections"],
    # responses={200: "Successful response"},
)
