from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient, ShopCart,
                     Subscription, Tag)


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1
    raw_id_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_image', 'author', 'pub_date')
    fields = ('name', 'get_image', 'image', 'author',
              'tags', 'text', 'cooking_time', 'count_fav')
    readonly_fields = ('get_image', 'count_fav')
    list_select_related = ('author',)
    raw_id_fields = ('tags',)
    inlines = (IngredientInline,)
    list_per_page = 6
    list_filter = ('author', 'tags')
    search_fields = ('name',)

    @admin.display(description='Кол-во добавлений в избранное')
    def count_fav(self, obj):
        return obj.favorites.count()

    @admin.display(description='Картинка')
    def get_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" height="80"')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    list_display_links = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('name',)
    list_per_page = 20
    search_fields = ('^name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    list_filter = ('owner',)
    search_fields = ('recipe__name', 'owner__username', 'owner__first_name')


@admin.register(ShopCart)
class ShopCartAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    list_filter = ('owner',)
    search_fields = ('recipe__name', 'owner__username', 'owner__first_name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    list_filter = ('user', 'author')
    search_fields = ('user__username', 'user__first_name')
