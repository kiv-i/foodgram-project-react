from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import MinValueValidator, RegexValidator

User = get_user_model()


class AbstractRecipeOwner(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name=_('Рецепт')
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name=_('Пользователь')
    )

    class Meta:
        abstract = True


class Recipe(models.Model):
    tags = models.ManyToManyField(
        'Tag',
        related_name='recipes',
        verbose_name=_('Список тегов'),
        db_table='RecipeTag',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name=_('Автор'),
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name=_('Список ингредиентов'),
    )
    name = models.CharField(_('Название'), max_length=200, unique=True)
    image = models.ImageField(_('Картинка'), upload_to='recipe/img/')
    text = models.TextField(_('Описание'))
    cooking_time = models.PositiveSmallIntegerField(
        _('Время готовки'),
        validators=[
            MinValueValidator(
                limit_value=1,
                message=_('Значение не должно быть меньше 1 минуты.'),
            )],
        help_text=_('Время приготовления (в минутах).'),
    )
    pub_date = models.DateTimeField(_('Дата публикации'), auto_now_add=True)

    class Meta:
        ordering = ['-pub_date']
        verbose_name = _('Рецепт')
        verbose_name_plural = _('Рецепты')

    def __str__(self) -> str:
        return self.name

    def delete(self, *args, **kwargs):
        path = Path(self.image.path)
        super().delete(*args, **kwargs)
        # Удалить файл картинки при удалении рецепта.
        if path:
            path.unlink(missing_ok=True)

    def save(self, *args, **kwargs):
        # Удалить старый файл картинки при обновлении.
        try:
            path = Path(Recipe.objects.get(pk=self.pk).image.path)
        except Recipe.DoesNotExist:
            path = None
        super().save(*args, **kwargs)
        if path:
            path.unlink(missing_ok=True)


class Ingredient(models.Model):
    name = models.CharField(_('Название'), max_length=200)
    measurement_unit = models.CharField(_('Единица измерения'), max_length=200)

    class Meta:
        ordering = ['name']
        verbose_name = _('Ингредиент')
        verbose_name_plural = _('Ингредиенты')

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(_('Название'), max_length=200, unique=True)
    color = models.CharField(
        _('Цвет'),
        max_length=7,
        validators=[
            RegexValidator(regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
        ],
        help_text=_('Цвет в формате HEX'),
    )
    slug = models.SlugField(
        _('Уникальный слаг'),
        max_length=200,
        unique=True,
    )

    class Meta:
        verbose_name = _('Тег')
        verbose_name_plural = _('Теги')

    def __str__(self) -> str:
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name=_('Ингредиент'),
    )
    amount = models.PositiveSmallIntegerField(
        _('Количество'),
        validators=[
            MinValueValidator(
                limit_value=1,
                message=_('Введите целое число.')
            )],
    )

    class Meta:
        verbose_name = _('Ингредиент')
        verbose_name_plural = _('Ингредиенты рецепта')


class ShopCart(AbstractRecipeOwner):
    class Meta:
        verbose_name = _('Список покупок')
        verbose_name_plural = _('Списки покупок')

    def __str__(self) -> str:
        return f'"{self.recipe}" в списке покупок пользователя - {self.owner}'


class Favorite(AbstractRecipeOwner):
    class Meta:
        verbose_name = _('Избранный рецепт')
        verbose_name_plural = _('Избранные рецепты')

    def __str__(self):
        return (f'"{self.recipe}" в избранных '
                f'у пользователя - {self.owner.first_name}')


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name=_('Пользователь'),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name=_('Автор рецепта'),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='not_subscription_yourself'
            ),
        ]
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')

    def __str__(self) -> str:
        return (f'{self.user.first_name} подписан(а) '
                f'на - {self.author.first_name}')
