from rest_framework import serializers
from .models import Video, VideoCategory


class VideoCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = VideoCategory
        fields = ("id", "name", "slug", "icon", "sort_order")


class VideoSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model  = Video
        fields = (
            "id", "title", "description",
            "youtube_url", "youtube_id", "thumbnail_url",
            "category", "category_name",
            "target_audience", "is_featured", "is_active",
            "created_at",
        )
        read_only_fields = ("id", "youtube_id", "thumbnail_url", "created_at")


class CreateVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Video
        fields = (
            "title", "description", "youtube_url",
            "category", "target_audience", "is_featured",
        )

    def validate_youtube_url(self, value):
        if "youtube.com" not in value and "youtu.be" not in value:
            raise serializers.ValidationError("Please provide a valid YouTube URL.")
        return value