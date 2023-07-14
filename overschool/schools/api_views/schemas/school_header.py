from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class SchoolHeaderSchemas:
    def default_schema():
        return swagger_auto_schema(
            tags=["school_header"],
        )

    def partial_update_schema():
        return swagger_auto_schema(
            tags=["school_header"],
            manual_parameters=[
                openapi.Parameter(
                    name="name",
                    in_=openapi.IN_FORM,
                    description="Главное название школы в шапке",
                    type=openapi.TYPE_STRING,
                    required=False,
                ),
                openapi.Parameter(
                    name="school",
                    in_=openapi.IN_FORM,
                    description="id школы, котрой принадлежит header",
                    type=openapi.TYPE_INTEGER,
                    required=False,
                ),
            ],
        )
