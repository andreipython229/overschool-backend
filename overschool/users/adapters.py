import logging

from allauth.account.models import EmailAddress
from allauth.account.utils import perform_login
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.signals import pre_social_login
from allauth.utils import get_user_model
from django.conf import settings

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Регистрация и логинизация пользователя через соцсеть.
        """
        if sociallogin.is_existing:
            logger.debug(
                f"Social login: Account already exists and is linked for {sociallogin.user.email}"
            )
            return

        try:
            email = sociallogin.account.extra_data.get("email")
            if not email and sociallogin.email_addresses:
                email = sociallogin.email_addresses[0].email

            if not email:
                logger.warning("Social login: Email not provided by social account.")
                return

            User = get_user_model()
            existing_user = User.objects.get(email__iexact=email)

            logger.info(
                f"Social login: Auto-connecting existing user {email} with social account."
            )
            sociallogin.connect(request, existing_user)

            perform_login(
                request,
                existing_user,
                email_verification=settings.ACCOUNT_EMAIL_VERIFICATION,
                redirect_url=settings.LOGIN_REDIRECT_URL,
                signal_kwargs={"sociallogin": sociallogin},
            )

        except User.DoesNotExist:
            logger.debug(
                f"Social login: No existing user found for email {email}. Proceeding with standard signup."
            )
        except Exception as e:
            logger.error(
                f"Error in pre_social_login for email {email}: {e}", exc_info=True
            )
