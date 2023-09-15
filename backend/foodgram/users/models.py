from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(
        _('email адрес'),
        unique=True,
        error_messages={
            'unique': _('Пользователь с таким email уже существует.'),
        },
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
