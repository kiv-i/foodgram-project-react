from django.db.models import F
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers, validators

from users.serializers import CustomUserSerializer
from .models import Ingredient, Recipe, RecipeIngredient, Tag, User
from .utils import Base64ImageField, ingredient_create


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Ingredient.objects.all(),
                fields=('name', 'measurement_unit'),
                message=_('Ингредиент с такими параметрами уже существует.')
            )
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Tag.objects.all(),
                fields=('name', 'color', 'slug'),
                message=_('Тег с такими параметрами уже существует.')
            )
        ]


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'author',
            'tags',
            'ingredients',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipe_ingredient__amount'),
        )

    def get_is_favorited(self, obj):
        current_user = self.context['request'].user
        if current_user.is_authenticated:
            try:
                is_fav = obj.is_fav
            except AttributeError:
                is_fav = obj.favorites.filter(owner=current_user).exists()
        else:
            is_fav = False
        return is_fav

    def get_is_in_shopping_cart(self, obj):
        current_user = self.context['request'].user
        if current_user.is_authenticated:
            try:
                is_in_shop = obj.is_shop
            except AttributeError:
                is_in_shop = obj.shopcarts.filter(owner=current_user).exists()
        else:
            is_in_shop = False
        return is_in_shop


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient_id')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    image = Base64ImageField(use_url=True)
    ingredients = RecipeIngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'tags',
            'ingredients',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        if not data.get('tags'):
            raise serializers.ValidationError(
                _('Пожалуйста, укажите теги.'))
        if not data.get('ingredients'):
            raise serializers.ValidationError(
                _('Пожалуйста, укажите ингредиенты.'))
        return data

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                _('Пожалуйста, добавьте ингредиенты.')
            )
        list_id = []
        for ingredient in ingredients:
            ingredient_id = ingredient.get('ingredient_id')
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise exceptions.ValidationError(
                    _(f'id: {ingredient_id} нет. Пожалуйста, '
                      'введите ID ингредиента из существующего списка.'),
                )
            list_id.append(ingredient_id)
        if len(list_id) != len(set(list_id)):
            raise serializers.ValidationError(
                _('Вы добавили несколько одинаковых ингредиентов.')
            )
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                _('Пожалуйста, добавьте теги.')
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                _('Вы добавили несколько одинаковых тегов.')
            )
        return tags

    @atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        ingredient_create(recipe, ingredients)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        ingredient_create(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class RecipeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context['request']
        recipes = obj.recipes.all()
        if recipes_limit := request.query_params.get('recipes_limit'):
            recipes = recipes[:int(recipes_limit)]
        return RecipeListSerializer(
            recipes, many=True, context=self.context
        ).data
