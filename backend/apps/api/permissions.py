"""Права доступа для API WebApp: требуется успешная аутентификация по initData."""
from rest_framework import permissions


class TelegramUserRequired(permissions.BasePermission):
    """Требует наличие request.user (TelegramUser из initData)."""

    def has_permission(self, request, view):
        return request.user is not None
