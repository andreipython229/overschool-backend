from common_services.mixins import WithHeadersViewSet
from homeworks.models import UserHomework
from homeworks.serializers import UserHomeworkSerializer, UserHomeworkStatisticsSerializer
from rest_framework import viewsets
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models.expressions import Window
from django.db.models import F, Max, Q
from homeworks.paginators import UserHomeworkPagination


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
            queryset = self.get_queryset(**serializer.data)
            paginator = self.pagination_class()
            data = paginator.paginate_queryset(request=request, queryset=queryset)
            return paginator.get_paginated_response(data=data)
        else:
            return Response(data=serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        queryset = UserHomework.objects.filter(
            Q(updated_at__gte=kwargs['start_date'])
            & Q(updated_at__lte=kwargs['end_date'])
        )
        try:
            queryset = queryset.filter(Q(mark__gte=kwargs['start_mark'])
                                       & Q(mark__lte=kwargs['end_mark']))
        except KeyError:
            pass
        if kwargs['status']:
            queryset = queryset.filter(status=kwargs['status'])
        if kwargs['homework_id']:
            queryset = queryset.filter(homework_id__in=kwargs['homework_id'])
        if kwargs['course_id']:
            queryset = queryset.filter(homework__lesson__section__course__id=kwargs['course_id'])
        if kwargs['group_id']:
            queryset = queryset.filter(user__pk=kwargs['group_id'])
        return queryset.values('mark',
                               'status',
                               user_homework=F('homework_id'),
                               email=F('user__email'),
                               avatar=F('user__profile__avatar'),
                               homework_name=F('homework__lesson__section__course__name'),
                               homework_pk=F('homework__homework_id'),
                               lesson_name=F('homework__lesson__name'),
                               last_update=Window(expression=Max('updated_at'),
                                                  partition_by=[F('user__email'),
                                                                F('homework__homework_id')]))

# class HomeworkListView(generics.ListAPIView):
#     queryset = UserHomework.objects.all()
#     serializer_class = UserHomeworkSerializer
#     permission_classes = [permissions.AllowAny]
#     filter_backends = (DjangoFilterBackend)
#     filterset_class = HomeworkFilter
#

# class StudentsGroupFilter(filters.FilterSet):
#     group_id = filters.CharFilter(field_name="group_id", lookup_expr="icontains")
#     name = filters.CharFilter(field_name="name", lookup_expr="icontains")
#     teacher_id = filters.CharFilter(field_name="teacher__id", lookup_expr="icontains")
#     course = filters.CharFilter(field_name="course__id", lookup_expr="icontains")
#     students = filters.CharFilter(field_name="students__name", lookup_expr="icontains")
#
#     class Meta:
#         model = StudentsGroup
#         fields = ["group_id", "name", "teacher_id", "course", "students"]
#
# class StudentsGroupViewSet(WithHeadersViewSet, viewsets.ModelViewSet, ):
#     queryset = StudentsGroup.objects.all()
#     serializer_class = StudentsGroupSerializer
#     permission_classes = [permissions.AllowAny]
#     filter_backends = (DjangoFilterBackend,)
#     filterset_class = StudentsGroupFilter
