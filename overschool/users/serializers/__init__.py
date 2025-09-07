from .access_distribution import AccessDistributionSerializer
from .feedback import FeedbackSerializer
from .forgot_password_serializer import (
    ForgotPasswordSerializer,
    PasswordResetSerializer,
)
from .login import LoginSerializer
from .profile import (
    EmailValidateSerializer,
    UserProfileGetSerializer,
    UserProfileSerializer,
)
from .register import PasswordChangeSerializer, SignupSerializer
from .register_school_owner import CreateSchoolSerializer, SignupSchoolOwnerSerializer
from .tariff import TariffSerializer  # Добавляем импорт для TariffSerializer
from .user import AllUsersSerializer, UserSerializer
from .user_role import UserRoleSerializer