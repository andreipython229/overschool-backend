from drf_yasg import openapi


class FileParams:
    base_lesson = openapi.Parameter(
        "base_lesson",
        openapi.IN_FORM,
        description="base_lesson ID",
        type=openapi.TYPE_INTEGER,
    )
    user_homework = openapi.Parameter(
        "user_homework",
        openapi.IN_FORM,
        description="user_homework ID",
        type=openapi.TYPE_INTEGER,
    )
    user_homework_check = openapi.Parameter(
        "user_homework_check",
        openapi.IN_FORM,
        description="user_homework_check ID",
        type=openapi.TYPE_INTEGER,
    )
    files = openapi.Parameter(
        "files",
        openapi.IN_FORM,
        description="Files",
        type=openapi.TYPE_ARRAY,
        items=openapi.Items(type=openapi.TYPE_FILE),
        required=True,
    )
