from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Собственная модель пользователя,
    если в будущем захотим скорректировать поля."""
