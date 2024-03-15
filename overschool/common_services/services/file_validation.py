import os

from django.utils.deconstruct import deconstructible
from rest_framework import serializers


def limit_size(file):
    if file and file.size > 200 * 1024 * 1024:
        raise serializers.ValidationError("Размер файла не может превышать 200 МБ")


@deconstructible
class TruncateFileName:
    def __init__(self, max_length):
        self.max_length = max_length

    def __call__(self, instance, filename):
        name, extension = os.path.splitext(filename)
        if len(name) > self.max_length:
            name = name[: self.max_length]
        return f"{name}{extension}"
