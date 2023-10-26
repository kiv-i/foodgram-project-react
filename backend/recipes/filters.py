from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters

from .models import Recipe


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(
        field_name='favorites',
        label=_('В избранных'),
        method='filter_owner',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='shopcarts',
        label=_('В списке покупок'),
        method='filter_owner',
    )
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def filter_owner(self, queryset, name, value):
        lookup = '__'.join([name, 'owner'])
        if value := self.request.user.id:
            return queryset.filter(**{lookup: value})
        return queryset.filter(**{lookup: False})
