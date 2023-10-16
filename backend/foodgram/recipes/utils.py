import base64

from django.core.files.base import ContentFile
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response


def action_method(self, request, model, serializer, pk=None):
    """Обработка запросов /favorite и /shopping_cart"""
    owner = self.request.user
    try:
        recipe = self.get_object()
    except Http404:
        raise exceptions.ParseError(
            _('Вы пытаетесь добавить несуществующий рецепт.')
        )

    if request.method == 'DELETE':
        try:
            instance = get_object_or_404(model, owner=owner, recipe=recipe)
        except Http404:
            raise exceptions.ParseError(
                _(f'Такого рецепта нет в списке {model._meta.verbose_name}.')
            )
        instance.delete()
        return Response(
            _(f'Рецепт успешно удален из списка {model._meta.verbose_name}.'),
            status=status.HTTP_204_NO_CONTENT)

    if model.objects.filter(owner=owner, recipe=recipe).exists():
        raise exceptions.ParseError(
            _(f'Рецепт уже в списке {model._meta.verbose_name}.'))

    model.objects.create(owner=owner, recipe=recipe)
    serializer = serializer(recipe)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)
