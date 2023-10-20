from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            _('Personal info'),
            {
                'fields': (
                    'username',
                    'first_name',
                    'last_name'
                ),
            },
        ),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'admin',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'username',
                    'first_name',
                    'last_name',
                    'password1',
                    'password2'
                ),
            },
        ),
    )
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
        'admin',
    )
    search_fields = ('email', 'username')


admin.site.register(User, CustomUserAdmin)
