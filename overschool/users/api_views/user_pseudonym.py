from rest_framework import viewsets
from rest_framework.response import Response
from .models import UserPseudonym
from .serializers import UserPseudonymSerializer


class UserPseudonymViewSet(viewsets.ViewSet):
    """
    ViewSet для работы с псевдонимами сотрудников школы
    """
    
    queryset = UserPseudonym.objects.all()
    serializer_class = UserPseudonymSerializer

    def list(self, request):
        """
        Возвращает список всех псевдонимов сотрудников школы
        """

        queryset = UserPseudonym.objects.all()
        serializer = UserPseudonymSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Возвращает псевдоним сотрудника школы по его идентификатору
        """

        queryset = UserPseudonym.objects.all()
        user_pseudonym = get_object_or_404(queryset, pk=pk)
        serializer = UserPseudonymSerializer(user_pseudonym)
        return Response(serializer.data)

    def update(self, request, pk=None):
        """
        Обновляет псевдоним сотрудника
        """

        user = request.user
        school = request.data.get('school')
        user_pseudonym = UserPseudonym.objects.filter(user=user, school=school)
        user_pseudonym.save()
        return Response(serializer.errors, status=status.HTTP_200_OK)
