from .answer import AnswerGetSerializer, AnswerListGetSerializer, AnswerSerializer
from .course import (
    CourseGetSerializer,
    CourseSerializer,
    CourseStudentsSerializer,
    CourseWithGroupsSerializer,
)
from .homework import HomeworkDetailSerializer, HomeworkSerializer
from .lesson import LessonDetailSerializer, LessonSerializer, LessonUpdateSerializer,\
    LessonAvailabilitySerializer, LessonEnrollmentSerializer
from .lesson_components_order import LessonComponentsOrderSerializer
from .question import (
    QuestionGetSerializer,
    QuestionListGetSerializer,
    QuestionSerializer,
)
from .section import SectionSerializer, SectionRetrieveSerializer
from .section_test import TestSerializer
from .students_group import (
    GroupsInCourseSerializer,
    GroupStudentsSerializer,
    GroupUsersByMonthSerializer,
    StudentsGroupSerializer,
    StudentsGroupWTSerializer
)
from .students_group_settings import StudentsGroupSettingsSerializer
from .students_table_info import (
    StudentsTableInfoDetailSerializer,
    StudentsTableInfoSerializer,
)
from .user_homework import (
    UserHomeworkDetailSerializer,
    UserHomeworkSerializer,
    UserHomeworkStatisticsSerializer,
)
from .user_homework_check import (
    UserHomeworkCheckDetailSerializer,
    UserHomeworkCheckSerializer,
)
from .user_test import UserTestSerializer
