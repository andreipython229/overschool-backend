from django.shortcuts import render
from rest_framework import viewsets
from .models import VideoModel
from .serializers import VideoSerializer


class MainCourseModelView(viewsets.ModelViewSet):
    queryset = VideoModel.objects.all()
    serializer_class = VideoSerializer
