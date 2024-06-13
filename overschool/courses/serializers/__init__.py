from .answer import AnswerGetSerializer, AnswerListGetSerializer, AnswerSerializer
from .block import (
    BlockButtonSerializer,
    BlockDetailSerializer,
    BlockUpdateSerializer,
    LessonBlockSerializer,
    LessonOrderSerializer,
)
from .comment import CommentSerializer
from .course import (
    CourseGetSerializer,
    CourseSerializer,
    CourseStudentsSerializer,
    CourseWithGroupsSerializer,
    FolderSerializer,
)
from .course_appeals import CourseAppealsSerializer
from .folder_course import FolderCourseSerializer, FolderViewSerializer
from .homework import HomeworkDetailSerializer, HomeworkSerializer
from .lesson import (
    LessonAvailabilitySerializer,
    LessonDetailSerializer,
    LessonEnrollmentSerializer,
    LessonSerializer,
    LessonUpdateSerializer,
)
from .question import (
    QuestionGetSerializer,
    QuestionListGetSerializer,
    QuestionSerializer,
)
from .section import (
    SectionOrderSerializer,
    SectionRetrieveSerializer,
    SectionSerializer,
)
from .section_test import TestSerializer
from .students_group import (
    GroupCourseAccessSerializer,
    GroupsInCourseSerializer,
    GroupStudentsSerializer,
    GroupUsersByMonthSerializer,
    MultipleGroupCourseAccessSerializer,
    StudentsGroupSerializer,
    StudentsGroupWTSerializer,
)
from .students_group_settings import StudentsGroupSettingsSerializer
from .students_table_info import (
    StudentsTableInfoDetailSerializer,
    StudentsTableInfoSerializer,
)
from .students_training_duration import TrainingDurationSerializer
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
