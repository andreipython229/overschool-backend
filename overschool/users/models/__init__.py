# users/models/__init__.py
from .tariff import Tariff
from .feedback import Feedback
from .profile import Profile
from .user import User
from .user_pseudonym import UserPseudonym
from .user_role import UserGroup, UserRole
from .user_subscription import UserSubscription

# Закомментированные импорты (если они не используются)
# from .utm_label import UtmLabel
# from users.managers import UserManager

__all__ = [
    'Tariff',
    'Feedback',
    'Profile',
    'User',
    'UserPseudonym',
    'UserGroup',
    'UserRole',
    'UserSubscription',
    # 'UtmLabel',
]