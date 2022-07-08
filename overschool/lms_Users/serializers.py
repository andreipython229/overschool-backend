from rest_framework import serializers
from .models import User, Course


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('__all__')


class CourseSerializer(serializers.Serializer):
    """
    Serializer that will be used to deserialize the json to be then imported in the datawarehouse
    """
    name = serializers.CharField(max_length=256)
    description = serializers.CharField()
    duration = serializers.IntegerField()
    status = serializers.CharField(max_length=256)
    price = serializers.DecimalField(decimal_places=2,
                                     max_digits=15)
    photo = serializers.ImageField()


    def save(self):
        """
        Overwrite the save function on the serializer to be able to control
        how we want to insert / update the data provided by the source in our
        datawarehouse.
        """
        # First update or create the person
        course_obj, created = Course.objects.update_or_create(self)