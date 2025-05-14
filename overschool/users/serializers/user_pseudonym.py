from rest_framework import serializers
from ..models.user_pseudonym import UserPseudonym


class UserPseudonymSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели псевдонима сотрудника школы
    """
    class Meta:
        model = UserPseudonym
        fields = ['id', 'user', 'school', 'pseudonym']