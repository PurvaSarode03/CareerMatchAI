from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "target_role", "location")
    search_fields = ("user__username", "user__email", "target_role")
