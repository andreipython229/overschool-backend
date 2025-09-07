# fix_tariff.py
import os
import django

# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'overschool.settings')
django.setup()

from django.db import connection
from users.models import Tariff


def fix_database():
    # Добавляем недостающие поля
    with connection.cursor() as cursor:
        cursor.execute('''
            ALTER TABLE users_tariff 
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS description TEXT,
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        ''')

    # Создаём тариф Junior
    Tariff.objects.get_or_create(
        name='Junior',
        defaults={'price': 0, 'description': 'Стартовый тариф', 'is_active': True}
    )
    print("✅ Таблица users_tariff успешно обновлена")


if __name__ == '__main__':
    fix_database()