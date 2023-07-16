from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class SectionsSchemas:
    def default_schema():
        return swagger_auto_schema(
            tags=["sections"],
        )

    def partial_update_schema():
        return swagger_auto_schema(
            tags=["sections"],
            manual_parameters=[
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
                openapi.Parameter(
                    name="course",
                    in_=openapi.IN_FORM,
                    description="id курса которому принадлежит секция",
                    type=openapi.TYPE_INTEGER,
                    required=False,
                ),
            ],
        )
