from djoser.views import UserViewSet as DjoserViewSet
from recipes.views import SubscriptionViewSet


class UserViewSet(DjoserViewSet, SubscriptionViewSet):
    pass
