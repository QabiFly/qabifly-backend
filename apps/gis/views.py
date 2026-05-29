from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from core.responses import success_response, error_response
from core.permissions import IsAdminUser
from .models import Landmark, DeliveryZone
from .serializers import (
    LandmarkSerializer,
    DeliveryZoneSerializer,
    CheckPointInZoneSerializer,
)


class LandmarkListView(generics.ListAPIView):
    """GET /api/v1/gis/landmarks/?type=SCHOOL&village=Reoti"""
    permission_classes = [AllowAny]
    serializer_class   = LandmarkSerializer

    def get_queryset(self):
        qs = Landmark.objects.filter(is_active=True)
        ltype   = self.request.query_params.get("type")
        village = self.request.query_params.get("village")
        if ltype:
            qs = qs.filter(landmark_type=ltype.upper())
        if village:
            qs = qs.filter(village__icontains=village)
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class AdminCreateLandmarkView(APIView):
    """POST /api/v1/gis/admin/landmarks/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = LandmarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        landmark = serializer.save(added_by=request.user)
        return success_response(
            data=LandmarkSerializer(landmark).data,
            message="Landmark added.",
            status_code=status.HTTP_201_CREATED,
        )

    def delete(self, request, landmark_id):
        try:
            landmark = Landmark.objects.get(id=landmark_id)
        except Landmark.DoesNotExist:
            return error_response(message="Landmark not found.", status_code=404)
        landmark.is_active = False
        landmark.save(update_fields=["is_active"])
        return success_response(message="Landmark removed.")


class DeliveryZoneListView(generics.ListAPIView):
    """GET /api/v1/gis/zones/"""
    permission_classes = [AllowAny]
    serializer_class   = DeliveryZoneSerializer
    queryset = DeliveryZone.objects.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class CheckPointInZoneView(APIView):
    """
    POST /api/v1/gis/zones/check/
    Check if a GPS point falls within any delivery zone.
    Flutter uses this to validate delivery address.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CheckPointInZoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lat = float(serializer.validated_data["latitude"])
        lon = float(serializer.validated_data["longitude"])

        zones = DeliveryZone.objects.filter(is_active=True)
        matched = []
        for zone in zones:
            if zone.contains_point(lat, lon):
                matched.append(DeliveryZoneSerializer(zone).data)

        return success_response(data={
            "is_deliverable": len(matched) > 0,
            "zones":          matched,
        })


class AdminCreateZoneView(APIView):
    """POST /api/v1/gis/admin/zones/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = DeliveryZoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        zone = serializer.save()
        return success_response(
            data=DeliveryZoneSerializer(zone).data,
            message="Delivery zone created.",
            status_code=status.HTTP_201_CREATED,
        )