import csv

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext_lazy as _
from foodgram import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = _('Загрузка ингредиентов в базу данных.')

    def handle(self, *args, **options):
        try:
            path = settings.BASE_DIR / 'data' / 'ingredients.csv'
            with open(path, encoding='utf-8') as csv_file:
                reader = csv.reader(csv_file)
                ingredients = [
                    Ingredient(
                        name=row[0], measurement_unit=row[1],
                    ) for row in reader
                ]
                Ingredient.objects.bulk_create(ingredients)
                print(_('Ингредиенты успешно загружены.'))
        except FileNotFoundError:
            raise CommandError(
                _('Убедитесь, что ingredients.csv находится в ./data/'))
