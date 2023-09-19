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
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
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
        verbose_name=_('Список ингридиентов'),
    )
    name = models.CharField(_('Название'), max_length=200)
    image = models.ImageField(_('Картинка'), upload_to='recipe/img/')
    text = models.TextField(_('Описание'))
    cooking_time = models.PositiveSmallIntegerField(
        _('Время'),
        validators=[
            MinValueValidator(
                limit_value=1,
                message=_('Значение не должно быть меньше 1 минуты.'),
            )],
        help_text=_('Время приготовления (в минутах).'),
    )
    pub_date = models.DateTimeField(_('Дата публикации'), auto_now_add=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ['-pub_date']
        verbose_name = _('Рецепт')
        verbose_name_plural = _('Рецепты')


class Ingredient(models.Model):
    name = models.CharField(_('Название'), max_length=200, unique=True)
    measurement_unit = models.CharField(_('Единица измерения'), max_length=200)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _('Ингридиент')
        verbose_name_plural = _('Ингридиенты')


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
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        _('Количество'),
        validators=[
            MinValueValidator(
                limit_value=1,
                message=_('Введите целое число.')
            )],
        blank=True,
    )


class ShopCart(AbstractRecipeOwner):
    class Meta:
        verbose_name = _('Список покупок')

    def __str__(self) -> str:
        return f'Список покупок пользователя {self.owner}'


class Favorite(AbstractRecipeOwner):
    class Meta:
        verbose_name = _('Избранное')


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Автор рецепта',
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
        return f'{self.user} подписан на {self.author}.'
