from common_services.mixins import LoggingMixin, WithHeadersViewSet
from homeworks.models import Homework
from homeworks.serializers import HomeworkSerializer
from rest_framework import permissions, viewsets
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import permissions, mixins, status


class HomeworkViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def retrieve(self, request, *args, **kwargs):
        homework_id = self.kwargs['pk']

        try:
            instance = Homework.objects.get(homework_id=homework_id)
            serializer = self.get_serializer(instance)
            return Response(serializer.data|{"type": "homework"})
        except ObjectDoesNotExist:
            return Response({"status": "Error", "message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
