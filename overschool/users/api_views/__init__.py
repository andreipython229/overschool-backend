from .access_distribution import AccessDistributionView
from .forgot_password import ForgotPasswordView, PasswordResetView, TokenValidateView
from .login import LoginView, SocialLoginCompleteView
from .logout import LogoutView
from .profile import EmailValidateView, ProfileViewSet
from .register import PasswordChangeView, SendPasswordView, SignupView
from .register_school_owner import SignupSchoolOwnerView
from .tariff_school_owner import TariffSchoolOwner
from .user_pseudonym import UserPseudonymViewSet
from .user_schools import UserSchoolsView
from .users import AllUsersViewSet, GetCertificateView, UserViewSet
