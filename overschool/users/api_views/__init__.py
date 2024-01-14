from .access_distribution import AccessDistributionView
from .forgot_password import ForgotPasswordView, PasswordResetView, TokenValidateView
from .login import LoginView
from .logout import LogoutView
from .profile import ProfileViewSet
from .register import PasswordChangeView, SendPasswordView, SignupView
from .register_school_owner import SignupSchoolOwnerView
from .tariff_school_owner import TariffSchoolOwner
from .user_schools import UserSchoolsView
from .users import AllUsersViewSet, UserViewSet, GetCertificateView
