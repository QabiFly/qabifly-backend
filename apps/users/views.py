from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from core.responses import success_response, error_response
from .models import User
from .serializers import UserProfileSerializer, UserProfileUpdateSerializer


class MeView(APIView):
    """GET /api/v1/users/me/ — logged-in user ka profile"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return success_response(data=serializer.data)


class UpdateProfileView(generics.UpdateAPIView):
    """PATCH /api/v1/users/me/update/ — profile update"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=UserProfileSerializer(instance).data,
            message="Profile updated successfully",
        )


class DeleteAccountView(APIView):
    """DELETE /api/v1/users/me/delete/ — soft delete"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        return success_response(message="Account deactivated successfully")