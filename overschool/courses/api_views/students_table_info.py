from django.core.exceptions import ObjectDoesNotExist
from rest_framework import mixins, permissions, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from courses.models import StudentsTableInfo
from courses.serializers import StudentsTableInfoSerializer


class StudentsTableInfoViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    ''' Эндпоинт табличной информации о студентах\n
        Табличная информация о студентах
    '''
    queryset = StudentsTableInfo.objects.all()
    serializer_class = StudentsTableInfoSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs["pk"]

        try:
            instance = StudentsTableInfo.objects.get(admin=user_id)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"status": "Error", "message": "Not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        user_id = self.kwargs["pk"]

        try:
            instance = StudentsTableInfo.objects.get(admin=user_id)
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, "_prefetched_objects_cache", None):
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"status": "Error", "message": "Not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
