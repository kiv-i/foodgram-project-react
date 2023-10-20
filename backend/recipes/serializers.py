from django.db.models import F
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers
from rest_framework.validators import UniqueTogetherValidator
from users.serializers import CustomUserSerializer

from .models import Ingredient, Recipe, RecipeIngredient, Tag, User
from .utils import Base64ImageField


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )
        validators = [
            UniqueTogetherValidator(
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
            UniqueTogetherValidator(
                queryset=Tag.objects.all(),
                fields=('name', 'color', 'slug'),
                message=_('Тег с такими параметрами уже существует.')
            )
        ]


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()

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
        )

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipe_ingredient__amount'),
        )

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        current_user = self.context['request'].user
        if current_user.is_authenticated:
            try:
                rep['is_favorited'] = instance.is_fav
            except AttributeError:
                rep['is_favorited'] = \
                    instance.favorites.filter(owner=current_user).exists()
            try:
                rep['is_in_shopping_cart'] = instance.is_shop
            except AttributeError:
                rep['is_in_shopping_cart'] = \
                    instance.shopcarts.filter(owner=current_user).exists()
        return rep


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

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data

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
        objs = []
        for ingredient_amount in ingredients:
            ingredient_id = ingredient_amount.get('ingredient_id')
            amount = ingredient_amount.get('amount')
            ingredient = Ingredient.objects.get(id=ingredient_id)
            objs.append(RecipeIngredient(
                recipe=recipe, ingredient=ingredient, amount=amount
            ))
        RecipeIngredient.objects.bulk_create(objs)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = \
            validated_data.get('cooking_time', instance.cooking_time)
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()
            instance.tags.set(tags)
        else:
            raise serializers.ValidationError(
                _('Поле "tags" является обязательным полем.')
            )
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            for ingredient_amount in ingredients:
                ingredient_id = ingredient_amount.get('ingredient_id')
                ingredient = Ingredient.objects.get(id=ingredient_id)
                amount = ingredient_amount.get('amount')
                instance.ingredients.add(
                    ingredient, through_defaults={'amount': amount}
                )
        else:
            raise serializers.ValidationError(
                _('Поле "ingredients" является обязательным полем.')
            )
        instance.save()
        return instance


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
    recipes_count = serializers.SerializerMethodField()

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

    def get_recipes_count(self, obj):
        return obj.recipes.count()
