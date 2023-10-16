from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(
        verbose_name=_('email адрес'),
        unique=True,
        help_text=_('Обязательное поле.'),
        error_messages={
            'unique': _('Пользователь с таким email уже существует.'),
        },
    )
    first_name = models.CharField(
        _('Имя'),
        max_length=150,
        help_text=_('Обязательное поле.'),
    )
    last_name = models.CharField(
        _('Фамилия'),
        max_length=150,
        help_text=_('Обязательное поле.'),
    )
    admin = models.BooleanField(
        verbose_name=_('статус администратора'),
        default=False,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['id']
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

    def __str__(self) -> str:
        return self.username

    @property
    def is_admin(self) -> bool:
        return self.admin
