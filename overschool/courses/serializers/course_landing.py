from common_services.selectel_client import UploadToS3
from courses.serializers import SectionSerializer
from courses.models import (
    Course,
    Folder,
    CourseLanding,
    HeaderBlock,
    StatsBlock,
    BlockCards,
    AudienceBlock,
    TrainingProgram,
    TrainingPurpose,
)
from rest_framework import serializers

from .students_group import GroupsInCourseSerializer

s3 = UploadToS3()



class BlockCardsGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для карточек блока
    """

    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = BlockCards
        fields = [
            "id",
            "position",
            "photo",
            "photo_url",
            "title",
            "description",
        ]

    def get_photo_url(self, obj):
        if obj.photo:
            return s3.get_link(obj.photo.name)
        else:
            # Если нет загруженной картинки, вернуть ссылку на дефолтное изображение
            default_image_path = "base_course.jpg"
            return s3.get_link(default_image_path)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["photo"] = representation["photo_url"]
        del representation["photo_url"]
        return representation

class LandingGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор просмотра лендинга
    """
    header_block = serializers.SerializerMethodField()
    stats_block = serializers.SerializerMethodField()
    audience_block = serializers.SerializerMethodField()
    training_program_block = serializers.SerializerMethodField()
    training_purpose_block = serializers.SerializerMethodField()

    class Meta:
        model = CourseLanding
        fields = [
            "header_block",
            "stats_block",
            "audience_block",
            "training_program_block",
            "training_purpose_block",
        ]

    def get_header_block(self, obj):
        photo = obj.course.photo
        photo_url = ""
        if obj.course.photo:
            photo_url = s3.get_link(photo.name)
        else:
            # Если нет загруженной картинки, вернуть ссылку на дефолтное изображение
            default_image_path = "base_course.jpg"
            photo_url = s3.get_link(default_image_path)

        return {
            "id": obj.header.position,
            "content": "header",
            "visible": obj.header.is_visible,
            "onlyShow": True,
            "canUp": obj.header.can_up,
            "canDown": obj.header.can_down,
            "photoBackground": photo_url,
            "name": obj.course.name,
            "description": obj.course.description,
        }

    def get_stats_block(self, obj):
        # подсчёт числа занятий
        lessons_count = 0
        for section in obj.course.sections.all():
            lessons_count += section.lessons.count()

        return {
            "id": obj.stats.position,
            "content": "stats",
            "visible": obj.stats.is_visible,
            "canUp": obj.stats.can_up,
            "canDown": obj.stats.can_down,
            "lessonCount": lessons_count
        }

    def get_audience_block(self, obj):

        return {
            "id": obj.audience.position,
            "content": "audience",
            "visible": obj.audience.is_visible,
            "canUp": obj.audience.can_up,
            "canDown": obj.audience.can_down,
            "description": obj.audience.description,
            "chips": BlockCardsGetSerializer(obj.audience.chips.all().order_by('position'), many=True).data
        }

    def get_training_program_block(self, obj):
        # sections_dict = {}
        # for section in obj.course.sections.all():
        #     lessons = []
        #     for lesson in section.lessons.all():
        #         lessons.append(lesson.name)
        #     sections_dict[section.name] = lessons



        # sections_list = []
        # for section in obj.course.sections.all():
        #     lessons = []
        #     for lesson in section.lessons.all():
        #         lessons.append({
        #             "lesson_id": lesson.id,
        #             "section": lesson.section,
        #             "name": lesson.name,
        #             "order": lesson.order,
        #             "author_id": lesson.author_id,
        #             # "description": lesson.description,
        #             # "video": lesson.video,
        #             "points": lesson.points,
        #             "type": lesson.type,
        #             "all_components": lesson.all_components,
        #             "active": lesson.active,
        #             "lessonChecked": lesson.lessonChecked,
        #         })
        #
        #     sections_list.append({
        #         "section_id": section.section_id,
        #         "course": section.course,
        #         "name": section.name,
        #         "order": section.order,
        #         "lessons": lessons,
        #     })
        return {
            "id": obj.training_program.position,
            "content": "trainingProgram",
            "visible": obj.training_program.is_visible,
            "canUp": obj.training_program.can_up,
            "canDown": obj.training_program.can_down,
            "sections": SectionSerializer(obj.course.sections.all(),
                                          many=True).data
        }

    def get_training_purpose_block(self, obj):
        return {
            "id": obj.training_purpose.position,
            "content": "trainingPurpose",
            "visible": obj.training_purpose.is_visible,
            "canUp": obj.training_purpose.can_up,
            "canDown": obj.training_purpose.can_down,
            "description": obj.training_purpose.description,
            "chips": BlockCardsGetSerializer(obj.training_purpose.chips.all().order_by('position'), many=True).data
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["header"] = representation["header_block"]
        representation["stats"] = representation["stats_block"]
        representation["audience"] = representation["audience_block"]
        representation["trainingProgram"] = representation["training_program_block"]
        representation["trainingPurpose"] = representation["training_purpose_block"]
        del representation["header_block"]
        del representation["stats_block"]
        del representation["audience_block"]
        del representation["training_program_block"]
        del representation["training_purpose_block"]
        return representation

class CourseInfoSerializer(serializers.ModelSerializer):
    """
    Сериализатор для общей инфы по курсу курса
    """

    class Meta:
        model = Course
        fields = [
            "is_catalog",
            "is_direct",
            "public",
            "name",
            "format",
            "price",
            "description",
            "photo",
        ]


class HeaderLandingSerializer(serializers.ModelSerializer):
    """
    Сериализатор для шапки лендинга
    """
    class Meta:
        model = HeaderBlock
        fields = [
            "is_visible",
            "position",
            "can_up",
            "can_down",
        ]

class StatsGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор статистики курса
    """
    class Meta:
        model = StatsBlock
        fields = [
            "is_visible",
            "position",
            "can_up",
            "can_down",
        ]

class BlockCardsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    class Meta:
        model = BlockCards
        fields = [
            "id",
            "position",
            "title",
            "description",
        ]
        read_only_fields = ["id", "photo"]

    def update(self, instance, validated_data):
        # убираем ключи со значениями None из словаря
        for key, value in list(validated_data.items()):
            if value is None:
                del validated_data[key]

        instance.position = validated_data.get('position', instance.position)
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)

        instance.save()
        return instance

class BlockCardsPhotoSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    class Meta:
        model = BlockCards
        fields = [
            "id",
            "photo",
        ]

    def update(self, instance, validated_data):
        instance.photo = validated_data.get('photo', instance.photo)
        instance.save()
        return instance

class AudienceSerializer(serializers.ModelSerializer):
    """
    Сериализатор для блока с целевой аудиторией
    """
    chips = BlockCardsSerializer(many=True)

    class Meta:
        model = AudienceBlock
        fields = [
            "is_visible",
            "position",
            "can_up",
            "can_down",
            "description",
            "chips",
        ]

    def update(self, instance, validated_data):
        chips_data = validated_data.pop('chips', [])
        instance = super().update(instance, validated_data)

        # Обновление вложенных данных BlockCards
        chips_objs = []
        for chip_data in chips_data:
            chip_id = chip_data.get('id')
            if not (chip_id == -1):
                chip, _ = BlockCards.objects.update_or_create(
                            id=chip_id,
                            audienceblock=instance,
                            defaults={
                                'title': chip_data.get('title'),
                                'description': chip_data.get('description'),
                                # 'photo': chip_data.get('photo'),
                                'position': chip_data.get('position'),
                            }
                )
            else:
                try:
                    chip = BlockCards.objects.get(position=chip_data.get('position'))
                    chip.title = chip_data.get('title', chips_data.title)
                    chip.description = chip_data.get('description', chips_data.description)
                    # chip.photo = chip_data.get('photo', chips_data.photo)
                    chip.position = chip_data.get('position', chips_data.position)
                    chip.save()
                except:
                    chip = BlockCards.objects.create(
                        title=chip_data.get('title'),
                        description=chip_data.get('description'),
                        # photo=chip_data.get('photo'),
                        position=chip_data.get('position'),
                    )
            # if chip_id == -1:
            #     chip = BlockCards.objects.get(position=chip_data.get('position'))
            #     if not chip:
            #         chip = BlockCards.objects.create(
            #             title=chip_data.get('title'),
            #             description=chip_data.get('description'),
            #             photo=chip_data.get('photo'),
            #             position=chip_data.get('position'),
            #         )
            # else:
            #     chip, _ = BlockCards.objects.update_or_create(
            #         id=chip_id,
            #         audienceblock=instance,
            #         defaults={
            #             'title': chip_data.get('title'),
            #             'description': chip_data.get('description'),
            #             'photo': chip_data.get('photo'),
            #             'position': chip_data.get('position'),
            #         }
            #     )
            chips_objs.append(chip)

        instance.chips.set(chips_objs)
        instance.save()

        return instance

class TrainingProgramSerializer(serializers.ModelSerializer):
    """
    Сериализатор для блока с целевой аудиторией
    """

    class Meta:
        model = TrainingProgram
        fields = [
            "is_visible",
            "position",
            "can_up",
            "can_down",
        ]

class TrainingPurposeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для блока целей обучения курсу
    """
    chips = BlockCardsSerializer(many=True)

    class Meta:
        model = TrainingPurpose
        fields = [
            "is_visible",
            "position",
            "can_up",
            "can_down",
            "description",
            "chips",
        ]

    def update(self, instance, validated_data):
        chips_data = validated_data.pop('chips', [])
        instance = super().update(instance, validated_data)

        # Обновление вложенных данных BlockCards
        chips_objs = []
        for chip_data in chips_data:
            chip_id = chip_data.get('id')
            if chip_id == -1:
                chip = BlockCards.objects.create(
                    title=chip_data.get('title'),
                    description=chip_data.get('description'),
                    photo=chip_data.get('photo'),
                    position=chip_data.get('position'),
                )
            else:
                chip, _ = BlockCards.objects.update_or_create(
                    id=chip_data.get('id'),
                    trainingpurpose=instance,
                    defaults={
                        'title': chip_data.get('title'),
                        'description': chip_data.get('description'),
                        'photo': chip_data.get('photo'),
                        'position': chip_data.get('position'),
                    }
                )
            chips_objs.append(chip)

        instance.chips.set(chips_objs)
        instance.save()

        return instance
