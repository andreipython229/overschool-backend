from django.db import models
from ..models import Course, CourseName, CoursePhoto, CoursePrice, CourseStatus, CourseDuration, CourseDescription


class CourseManager(models.Manager):
    """
    Менеджер таблиц курсов
    """
    def update_or_create(self, *args, **kwargs):
        c = super().create({})
        self.save_name_attribute(c.course_id, kwargs['name'])
        return super().create(**kwargs)

    def save_name_attribute(self, course_id, name):
        cm = CourseName(course_id=course_id, name=name)
        cm.save()

    def save_description_attribute(self, course_id, description):
        cd = CourseDescription(course_id=course_id, description=description)
        cd.save()

    def save_status_attribute(self, course_id, status):
        ct = CourseStatus(course_id=course_id, status=status)
        ct.save()

    def save_price_attribute(self, course_id, price):
        cp = CoursePrice(course_id=course_id, price=price)
        cp.save()

    def save_photo_attribute(self, course_id, photo):
        cp = CoursePhoto(course_id=course_id, photo=photo)
        cp.save()
