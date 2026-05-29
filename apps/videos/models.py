import uuid
from django.db import models
from django.conf import settings


class VideoCategory(models.Model):
    name       = models.CharField(max_length=100, unique=True)
    slug       = models.SlugField(max_length=100, unique=True)
    icon       = models.CharField(max_length=50, blank=True)  # emoji or icon name
    sort_order = models.IntegerField(default=0)
    is_active  = models.BooleanField(default=True)

    class Meta:
        db_table  = "video_categories"
        ordering  = ["sort_order", "name"]
        verbose_name_plural = "Video Categories"

    def __str__(self):
        return self.name


class Video(models.Model):

    class TargetAudience(models.TextChoices):
        ALL       = "ALL",       "All Users"
        FARMERS   = "FARMERS",   "Farmers / Kisans"
        SHOPKEEPERS = "SHOPKEEPERS", "Shopkeepers"
        BUYERS    = "BUYERS",    "Buyers"

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category     = models.ForeignKey(
        VideoCategory, on_delete=models.PROTECT, related_name="videos"
    )
    title        = models.CharField(max_length=255)
    description  = models.TextField(blank=True)
    youtube_url  = models.URLField()
    youtube_id   = models.CharField(max_length=20)   # extracted from URL
    thumbnail_url = models.URLField(blank=True)       # auto-generated from youtube_id
    target_audience = models.CharField(
        max_length=20, choices=TargetAudience.choices, default=TargetAudience.ALL
    )
    is_featured  = models.BooleanField(default=False)
    is_active    = models.BooleanField(default=True)
    added_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="videos_added"
    )
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "videos"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Extract YouTube ID from URL and auto-set thumbnail
        if self.youtube_url and not self.youtube_id:
            self.youtube_id = self._extract_youtube_id(self.youtube_url)
        if self.youtube_id and not self.thumbnail_url:
            self.thumbnail_url = f"https://img.youtube.com/vi/{self.youtube_id}/hqdefault.jpg"
        super().save(*args, **kwargs)

    @staticmethod
    def _extract_youtube_id(url: str) -> str:
        import re
        patterns = [
            r"(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""