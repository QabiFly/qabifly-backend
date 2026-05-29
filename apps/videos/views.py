from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from core.responses import success_response, error_response
from core.permissions import IsAdminUser
from .models import Video, VideoCategory
from .serializers import VideoCategorySerializer, VideoSerializer, CreateVideoSerializer


class VideoCategoryListView(generics.ListAPIView):
    """GET /api/v1/videos/categories/"""
    permission_classes = [AllowAny]
    serializer_class   = VideoCategorySerializer
    queryset = VideoCategory.objects.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class VideoListView(generics.ListAPIView):
    """
    GET /api/v1/videos/?category=<slug>&audience=FARMERS&featured=true
    """
    permission_classes = [AllowAny]
    serializer_class   = VideoSerializer

    def get_queryset(self):
        qs = Video.objects.filter(is_active=True).select_related("category")
        category = self.request.query_params.get("category")
        audience = self.request.query_params.get("audience")
        featured = self.request.query_params.get("featured")
        search   = self.request.query_params.get("search")

        if category:
            qs = qs.filter(category__slug=category)
        if audience:
            qs = qs.filter(target_audience__in=["ALL", audience.upper()])
        if featured and featured.lower() == "true":
            qs = qs.filter(is_featured=True)
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class AdminCreateVideoView(APIView):
    """POST /api/v1/videos/admin/create/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = CreateVideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video = serializer.save(added_by=request.user)
        return success_response(
            data=VideoSerializer(video).data,
            message="Video added successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class AdminVideoListView(generics.ListAPIView):
    """GET /api/v1/videos/admin/list/"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class   = VideoSerializer
    queryset = Video.objects.select_related("category", "added_by").all()

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class AdminToggleVideoView(APIView):
    """POST /api/v1/videos/admin/<uuid:video_id>/toggle/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, video_id):
        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return error_response(message="Video not found.", status_code=404)
        video.is_active = not video.is_active
        video.save(update_fields=["is_active"])
        state = "activated" if video.is_active else "deactivated"
        return success_response(message=f"Video {state}.")