from django.shortcuts import render
from rest_framework import viewsets
from .models import MainCourseModel
from .serializers import CustomUserSerializer
from .permissions import IsAdminUserOrReadOnly


class MainCourseModelView(viewsets.ModelViewSet):
    queryset = MainCourseModel.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAdminUserOrReadOnly]
# Create your views here.
