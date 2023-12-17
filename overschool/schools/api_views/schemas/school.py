from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class SchoolsSchemas:
    def default_schema():
        return swagger_auto_schema(
            tags=["schools"],
        )

    def partial_update_schema():
        # Объединяем параметры из обеих схем
        parameters = [
            openapi.Parameter(
                name="name",
                in_=openapi.IN_FORM,
                description="Название школы",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                name="order",
                in_=openapi.IN_FORM,
                description="",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ]
        return swagger_auto_schema(
            tags=["schools"],
            manual_parameters=parameters,
        )

