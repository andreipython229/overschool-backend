from common_services.mixins import WithHeadersViewSet
from homeworks.models import UserHomework
from homeworks.serializers import UserHomeworkSerializer, UserHomeworkStatisticsSerializer
from rest_framework import viewsets
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models.expressions import Window
from django.db.models import F, Max, Q
from homeworks.paginators import UserHomeworkPagination
from django.core.paginator import Paginator


class HomeworkViewSet(WithHeadersViewSet, viewsets.ModelViewSet):
    queryset = UserHomework.objects.all()
    serializer_class = UserHomeworkSerializer
    permission_classes = [permissions.AllowAny]


class HomeworkStatisticsView(WithHeadersViewSet, generics.ListAPIView):
    serializer_class = UserHomeworkStatisticsSerializer
    queryset = UserHomework.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = UserHomeworkPagination

    def list(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                page = request.GET['page']
            except KeyError:
                page = 1
            queryset = UserHomework.objects.filter(
                Q(mark__gte=serializer.data['start_mark']) & Q(mark__lte=serializer.data['end_mark']) & Q(
                    updated_at__gte=serializer.data['start_date']) & Q(updated_at__lte=serializer.data['end_date']))
            paginator = Paginator(queryset, serializer.data['limit'])
            return Response(data=paginator.page(page).object_list.values('mark',
                                                 'status',
                                                 user_homework=F('homework_id'),
                                                 email=F('user__email'),
                                                 avatar=F('user__profile__avatar'),
                                                 homework_name=F('homework__lesson__section__course__name'),
                                                 homework_pk=F('homework__homework_id'),
                                                 lesson_name=F('homework__lesson__name'),
                                                 last_update=Window(expression=Max('updated_at'),
                                                                    partition_by=[F('user__email'),
                                                                                  F('homework__homework_id')])),
                            status=status.HTTP_200_OK)
        else:
            return Response(data=serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
