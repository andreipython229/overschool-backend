from .answer import AnswerViewSet
from .block import BaseLessonBlockViewSet, BlockButtonViewSet, BlockUpdateViewSet
from .comment import CommentViewSet
from .course import CourseViewSet
from .course_appeals import CourseAppealsViewSet, GetAppealsViewSet
from .course_catalog import CourseCatalogViewSet
from .folder_course import FolderCourseViewSet
from .homework import HomeworkViewSet
from .lesson import (
    LessonAvailabilityViewSet,
    LessonEnrollmentViewSet,
    LessonUpdateViewSet,
    LessonViewSet,
)
from .question import QuestionViewSet
from .section import SectionUpdateViewSet, SectionViewSet
from .section_test import TestViewSet
from .student_progress import StudentProgressViewSet
from .students_group import (
    GroupCourseAccessViewSet,
    StudentsGroupViewSet,
    StudentsGroupWithoutTeacherViewSet,
)
from .students_group_settings import StudentsGroupSettingsViewSet
from .students_table_info import StudentsTableInfoViewSet
from .students_training_duration import TrainingDurationViewSet
from .upload_video import UploadVideoViewSet
from .user_homework import HomeworkStatisticsView, UserHomeworkViewSet
from .user_homework_check import HomeworkCheckViewSet
from .user_test import UserTestViewSet
