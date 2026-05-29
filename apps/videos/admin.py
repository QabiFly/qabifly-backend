from django.contrib import admin
from .models import Video, VideoCategory


@admin.register(VideoCategory)
class VideoCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display  = ("title", "category", "target_audience", "is_featured", "is_active", "created_at")
    list_filter   = ("category", "target_audience", "is_featured", "is_active")
    search_fields = ("title",)
    readonly_fields = ("id", "youtube_id", "thumbnail_url", "created_at")