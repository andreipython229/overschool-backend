from django.core.management.base import BaseCommand
from users.models import Tariff

DEFAULT_TARIFFS = [
    {
        'name': 'Junior',
        'price': 0,
        'is_active': True,
        'description': 'Бесплатный начальный тариф'
    },
    {
        'name': 'Middle',
        'price': 1000,
        'is_active': True,
        'description': 'Стандартный тариф'
    },
    {
        'name': 'Senior',
        'price': 2000,
        'is_active': True,
        'description': 'Премиум тариф'
    }
]

class Command(BaseCommand):
    help = 'Создает стандартные тарифные планы'

    def handle(self, *args, **options):
        for tariff_data in DEFAULT_TARIFFS:
            tariff, created = Tariff.objects.get_or_create(
                name=tariff_data['name'],
                defaults=tariff_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан тариф: {tariff.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Тариф {tariff.name} уже существует'))