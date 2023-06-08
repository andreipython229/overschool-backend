from .answer import AnswerGetSerializer, AnswerSerializer
from .course import CourseGetSerializer, CourseSerializer, CourseStudentsSerializer
from .homework import (
    HomeworkDetailSerializer,
    HomeworkHistorySerializer,
    HomeworkSerializer,
)
from .lesson import LessonDetailSerializer, LessonSerializer
from .question import QuestionGetSerializer, QuestionSerializer
from .section import SectionSerializer
from .section_test import TestSerializer
from .students_group import (
    GroupStudentsSerializer,
    GroupUsersByMonthSerializer,
    StudentsGroupSerializer,
)
from .students_table_info import StudentsTableInfoSerializer
from .user_homework import (
    AllUserHomeworkDetailSerializer,
    AllUserHomeworkSerializer,
    TeacherHomeworkDetailSerializer,
    TeacherHomeworkSerializer,
    UserHomeworkDetailSerializer,
    UserHomeworkSerializer,
    UserHomeworkStatisticsSerializer,
)
from .user_test import UserTestSerializer
