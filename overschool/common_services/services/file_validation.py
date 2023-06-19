from rest_framework import serializers


def limit_size(file):
    if file and file.size > 20 * 1024 * 1024:
        raise serializers.ValidationError("Размер файла не может превышать 20 МБ")
