from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.exceptions import NotAuthenticated

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
        )

    def to_representation(self, instance):
        if instance.is_anonymous:
            raise NotAuthenticated()
        rep = super().to_representation(instance)
        cu = self.context.get('request').user
        if instance.id is not cu.id and not cu.is_anonymous:
            rep['is_subscribed'] = \
                instance.subscribing.filter(user=cu).exists()
        return rep


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
