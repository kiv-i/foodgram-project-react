from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from django.http import Http404, HttpResponse
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.fields import ObjectDoesNotExist
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import RecipeFilter
from .models import Favorite, Ingredient, Recipe, ShopCart, Subscription, Tag
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeListSerializer,
                          RecipeSerializer, RecipeWriteSerializer,
                          SubscriptionSerializer, TagSerializer)
from .utils import action_method

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author',
    ).prefetch_related(
        'ingredients', 'tags',
    )
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        cu = self.request.user
        queryset = super().get_queryset()
        if cu.is_anonymous:
            return queryset
        favorite = Favorite.objects.filter(recipe=OuterRef('pk'), owner=cu)
        shopcart = ShopCart.objects.filter(recipe=OuterRef('pk'), owner=cu)
        return queryset.annotate(
            is_fav=Exists(favorite)
        ).annotate(
            is_shop=Exists(shopcart)
        )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        author = self.request.user
        serializer.save(author=author)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        owner = self.request.user
        if not owner.shopcarts.exists():
            return Response(
                {_('Список покупок пуст.')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ingredients = Ingredient.objects.filter(
            recipes__shopcarts__owner=owner
        ).values(
            'name', 'measurement_unit',
        ).annotate(
            amount=Sum('recipe_ingredient__amount')
        )
        response = HttpResponse(
            content_type='text/plain',
            headers={
                'Content-Disposition': 'attachment; filename=shop_cart.txt'
            },
        )
        shop_cart = ['\u0332'.join(' СПИСОК ПОКУПОК:') + '\n\n',]

        for ingredient in ingredients:
            name = ingredient['name']
            measure = ingredient['measurement_unit']
            amount = ingredient['amount']
            shop_cart.append(f'\u2705 {name} ({measure}) \u268A {amount} \n')

        response.writelines(shop_cart)
        return response

    @action(['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        model = Favorite
        serializer = RecipeListSerializer
        return action_method(self, request, model, serializer, pk=None)

    @action(['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        model = ShopCart
        serializer = RecipeListSerializer
        return action_method(self, request, model, serializer, pk=None)


class SubscriptionViewSet():
    @action(['get'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscribers = self.queryset.filter(subscribing__user=request.user)
        page = self.paginate_queryset(subscribers)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        try:
            author = self.get_object()
        except Http404:
            raise exceptions.NotFound(
                _('Такой пользователь не зарегистрирован.'))

        if request.method == 'DELETE':
            try:
                subscribe = Subscription.objects.get(user=user, author=author)
                subscribe.delete()
                return Response({_('Успешная отписка.')},
                                status=status.HTTP_204_NO_CONTENT)
            except ObjectDoesNotExist:
                raise exceptions.ParseError(_('Такой подписки не найдено.'))

        if Subscription.objects.filter(user=user, author=author).exists():
            raise exceptions.ParseError(
                _('Вы уже подписаны на этого автора.')
            )
        if user == author:
            raise exceptions.ParseError(
                _('Нельзя подписаться на самого себя!')
            )
        Subscription.objects.create(user=user, author=author)
        serializer = SubscriptionSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
