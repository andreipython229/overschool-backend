from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

student_progress_example = {
    "student": "student_2@gmail.com",
    "school_id": 1,
    "school_name": "School_1",
    "courses": [
        {
            "course_id": 1,
            "course_name": "Java",
            "all_baselessons": 29,
            "completed_count": 7,
            "completed_perсent": 24.14,
            "lessons": {
                "completed_perсent": 60,
                "all_lessons": 5,
                "completed_lessons": 3,
            },
            "homeworks": {
                "completed_perсent": 0,
                "all_homeworks": 3,
                "completed_homeworks": 0,
            },
            "tests": {
                "completed_perсent": 19.05,
                "all_tests": 21,
                "completed_tests": 4,
            },
        },
        {
            "course_id": 3,
            "course_name": "Frontend",
            "all_baselessons": 5,
            "completed_count": 0,
            "completed_perсent": 0,
            "lessons": {
                "completed_perсent": 0,
                "all_lessons": 1,
                "completed_lessons": 0,
            },
            "homeworks": {
                "completed_perсent": 0,
                "all_homeworks": 1,
                "completed_homeworks": 0,
            },
            "tests": {"completed_perсent": 0, "all_tests": 3, "completed_tests": 0},
        },
    ],
}

error_structure = {
    "error": "string",
}

student_progress_schema_response = {
    "200": openapi.Response(
        description="OK", examples={"application/json": student_progress_example}
    ),
    "400": openapi.Response(
        description="Bad request", examples={"application/json": error_structure}
    ),
}


class StudentProgressSchemas:
    def student_progress_for_student_swagger_schema():
        return swagger_auto_schema(
            operation_description="""Эндпоинт прогресса прохождения курсов для студента\n
                /api/{school_name}/student_progress/get_student_progress/\n
                необходимо быть залогиненым под студентом\n
                """,
            operation_summary="Эндпоинт прогресса прохождения курсов",
            tags=["student_progress"],
            responses=student_progress_schema_response,
            manual_parameters=[
                openapi.Parameter(
                    name="course_id",
                    in_=openapi.IN_QUERY,
                    description="id курса",
                    type=openapi.TYPE_INTEGER,
                    required=True,
                )
            ],
        )

    def student_progress_for_admin_or_teacher_swagger_schema():
        return swagger_auto_schema(
            operation_description="""Эндпоинт прогресса прохождения курсов для АДМИНА и УЧИТЕЛЯ\n
                /api/{school_name}/student_progress/get_student_progress_for_admin_or_teacher/\n
                необходимо быть залогиненым под АДМИНОМ или УЧИТЕЛЕМ\n
                """,
            operation_summary="Эндпоинт прогресса прохождения курсов для АДМИНА и УЧИТЕЛЯ",
            tags=["student_progress"],
            responses=student_progress_schema_response,
            manual_parameters=[
                openapi.Parameter(
                    name="student_id",
                    in_=openapi.IN_QUERY,
                    description="id студента",
                    type=openapi.TYPE_INTEGER,
                    required=True,
                )
            ],
        )
