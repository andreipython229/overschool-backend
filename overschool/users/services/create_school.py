import logging

from django.contrib.auth.models import Group
from django.utils import timezone
from schools.models import (
    Referral,
    School,
    SchoolDocuments,
    SchoolHeader,
    Tariff,
    TariffPlan,
)
from users.models import User

logger = logging.getLogger(__name__)


def create_school_for_user(
    user: User, school_name: str, phone_number: str, referral_code: str = None
) -> School:
    """
    Сервисная функция для создания школы для указанного пользователя.
    """

    if School.objects.filter(owner=user).count() >= 2:
        raise ValueError("Пользователь может быть владельцем только двух школ.")

    if str(user.phone_number) != str(phone_number):
        user.phone_number = phone_number
        user.save(update_fields=["phone_number"])
        logger.info(f"Updated phone number for user {user.email}")

    trial_days = 14
    if referral_code:
        try:
            School.objects.get(referral_code=referral_code)
            trial_days += 21
        except School.DoesNotExist:
            logger.warning(
                f"Referral code {referral_code} provided but referrer school not found."
            )
            referral_code = None

    try:
        junior_tariff = Tariff.objects.get(name=TariffPlan.JUNIOR.value)
    except Tariff.DoesNotExist:
        logger.error(f"Tariff '{TariffPlan.JUNIOR.value}' not found!")
        raise ValueError(f"Тариф '{TariffPlan.JUNIOR.value}' не найден.")

    school = School(
        name=school_name,
        owner=user,
        tariff=junior_tariff,
        used_trial=True,
        trial_end_date=timezone.now() + timezone.timedelta(days=trial_days),
    )
    school.save()
    logger.info(f"School '{school.name}' created for user {user.email}")

    if referral_code:
        try:
            referrer_school = School.objects.get(referral_code=referral_code)
            Referral.objects.create(
                referrer_school=referrer_school, referred_school=school
            )
            logger.info(
                f"Referral link created: {referrer_school.name} -> {school.name}"
            )
        except School.DoesNotExist:
            logger.error(
                f"Referrer school with code {referral_code} not found during referral creation."
            )
        except Exception as e:
            logger.error(f"Error creating referral record: {e}", exc_info=True)

    SchoolHeader.objects.create(school=school, name=school.name)
    SchoolDocuments.objects.create(school=school, user=user)

    try:
        group = Group.objects.get(name="Admin")
        user.groups.create(group=group, school=school)
        logger.info(f"User {user.email} added to Admin group for school {school.name}")
    except Group.DoesNotExist:
        logger.error("Group 'Admin' not found!")
    except Exception as e:
        logger.error(f"Error assigning group to user: {e}", exc_info=True)

    return school
