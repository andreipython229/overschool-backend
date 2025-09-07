from django.apps import AppConfig
import logging
from django.db.models.signals import post_save, post_migrate
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = _("Пользователи")

    def ready(self):
        """
        Инициализация приложения с безопасной регистрацией сигналов
        и дополнительными проверками.
        """
        if not self._is_models_ready():
            logger.warning("Models are not ready yet. Skipping signal registration.")
            return

        self._register_signals()
        self._setup_permissions()

    def _is_models_ready(self):
        """Проверяет, загружены ли модели Django."""
        from django.apps import apps
        return apps.models_ready

    def _register_signals(self):
        """Регистрирует все сигналы приложения."""
        self._register_user_signals()
        self._register_school_signals()
        self._register_post_migrate()

    def _register_user_signals(self):
        """Регистрирует сигналы, связанные с пользователями."""
        try:
            from .signals.users_profile import create_profile, save_profile
            from .models import User

            post_save.disconnect(create_profile, sender=User)
            post_save.disconnect(save_profile, sender=User)

            post_save.connect(create_profile, sender=User, weak=False)
            post_save.connect(save_profile, sender=User, weak=False)
            logger.info("User signals successfully registered")
        except Exception as e:
            logger.error(f"Failed to register user signals: {e}", exc_info=True)

    def _register_school_signals(self):
        """Регистрирует сигналы, связанные со школами."""
        try:
            from .signals.role_signals import assign_admin_role
            from schools.models import School

            post_save.disconnect(assign_admin_role, sender=School)
            post_save.connect(assign_admin_role, sender=School, weak=False)
            logger.info("School signals successfully registered")
        except Exception as e:
            logger.error(f"Failed to register school signals: {e}", exc_info=True)

    def _register_post_migrate(self):
        """Регистрирует обработчик для post_migrate сигнала."""
        post_migrate.connect(self._create_initial_data, sender=self)

    def _create_initial_data(self, sender, **kwargs):
        """Создает начальные данные после миграций."""
        try:
            from .models import User
            if not User.objects.exists():
                self._create_superuser()
                logger.info("Initial data created successfully")
        except Exception as e:
            logger.error(f"Failed to create initial data: {e}", exc_info=True)

    def _create_superuser(self):
        """Создает суперпользователя по умолчанию."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin'
            )
            logger.info("Default superuser created")

    def _setup_permissions(self):
        """Настраивает разрешения для приложения."""
        try:
            from django.contrib.auth.management import create_permissions
            from django.apps import apps

            # Исключаем создание разрешений для User
            for app_config in apps.get_app_configs():
                if app_config.name != 'users':  # Не создаем разрешения для users
                    create_permissions(app_config)
            logger.debug("Permissions setup completed")
        except Exception as e:
            logger.error(f"Failed to setup permissions: {e}", exc_info=True)