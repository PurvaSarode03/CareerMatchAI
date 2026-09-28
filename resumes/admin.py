from django.contrib import admin

from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "full_name", "uploaded_at")
    search_fields = ("title", "user__username", "full_name")
    readonly_fields = ("raw_text", "embedding", "stats")
    exclude = ("embedding",)
