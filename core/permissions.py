from rest_framework.permissions import BasePermission


class IsBuyer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "BUYER"


class IsShopkeeper(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "SHOPKEEPER"


class IsDeliveryBoy(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "DELIVERY_BOY"


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "ADMIN"


class IsShopkeeperOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("SHOPKEEPER", "ADMIN")


class IsBuyerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("BUYER", "ADMIN")