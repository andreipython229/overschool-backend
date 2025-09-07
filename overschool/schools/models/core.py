# core.py
from django.db.models import ManyToManyField, ForeignKey

class CloneMixin:
    def clone(self):
        obj = self.__class__.objects.get(pk=self.pk)
        obj.pk = None
        obj.save()

        for field in self._meta.get_fields():
            if isinstance(field, ForeignKey):
                related_obj = getattr(self, field.name)
                setattr(obj, field.name, related_obj)

        obj.save()

        for field in self._meta.many_to_many:
            source_m2m = getattr(self, field.name).all()
            getattr(obj, field.name).set(source_m2m)

        return obj