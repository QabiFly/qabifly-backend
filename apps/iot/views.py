import logging
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny

from core.responses import success_response, error_response
from core.permissions import IsAdminUser
from .models import IoTNode
from .serializers import IoTNodeSerializer, SensorReadingIngestSerializer
from .mongo_utils import save_reading, get_latest_reading, get_readings_last_n_hours
from .crop_advisor import get_crop_advice

logger = logging.getLogger("apps")

# Simple device secret — set in .env
IOT_SECRET_KEY = getattr(settings, "IOT_SECRET_KEY", "qabifly-iot-secret-2024")


class IngestSensorDataView(APIView):
    """
    POST /api/v1/iot/ingest/
    ESP32 sensor yahan data bhejta hai.
    No JWT — device secret key se authenticate hota hai.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SensorReadingIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Device auth
        if data["secret_key"] != IOT_SECRET_KEY:
            return error_response(
                message="Invalid device secret key.", status_code=401
            )

        # Get or create node
        try:
            node = IoTNode.objects.get(node_id=data["node_id"])
        except IoTNode.DoesNotExist:
            return error_response(
                message=f"Node '{data['node_id']}' not registered.", status_code=404
            )

        # Save reading to MongoDB
        reading_data = {k: v for k, v in data.items()
                        if k not in ("node_id", "secret_key")}
        save_reading(data["node_id"], reading_data)

        # Update node status
        node.status       = IoTNode.Status.ACTIVE
        node.last_seen_at = timezone.now()
        node.save(update_fields=["status", "last_seen_at"])

        logger.info(f"IoT reading saved — node: {node.node_id}")
        return success_response(message="Reading saved.")


class CurrentWeatherView(APIView):
    """
    GET /api/v1/iot/weather/?node_id=REOTI-NODE-01
    Latest weather + crop advice.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        node_id = request.query_params.get("node_id")

        if node_id:
            nodes = IoTNode.objects.filter(node_id=node_id)
        else:
            nodes = IoTNode.objects.filter(status=IoTNode.Status.ACTIVE)

        if not nodes.exists():
            return error_response(message="No active IoT nodes found.", status_code=404)

        results = []
        for node in nodes:
            latest      = get_latest_reading(node.node_id)
            history     = get_readings_last_n_hours(node.node_id, hours=24)
            advice      = get_crop_advice(latest) if latest else []

            results.append({
                "node":        IoTNodeSerializer(node).data,
                "latest":      latest,
                "advice":      advice,
                "history_24h": history[:12],  # last 12 readings
            })

        return success_response(data=results)


class NodeListView(generics.ListAPIView):
    """GET /api/v1/iot/nodes/"""
    permission_classes = [AllowAny]
    serializer_class   = IoTNodeSerializer
    queryset = IoTNode.objects.all()

    def list(self, request, *args, **kwargs):
        # Auto-mark stale nodes
        from datetime import timedelta
        stale_threshold = timezone.now() - timedelta(minutes=30)
        IoTNode.objects.filter(
            status=IoTNode.Status.ACTIVE,
            last_seen_at__lt=stale_threshold,
        ).update(status=IoTNode.Status.STALE)

        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class AdminCreateNodeView(APIView):
    """POST /api/v1/iot/admin/nodes/create/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = IoTNodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        node = serializer.save()
        return success_response(
            data=IoTNodeSerializer(node).data,
            message=f"Node '{node.node_id}' registered.",
            status_code=201,
        )