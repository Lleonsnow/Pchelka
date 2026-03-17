from django.contrib import admin
from .models import BotSettings, SubscriptionChannel


@admin.register(SubscriptionChannel)
class SubscriptionChannelAdmin(admin.ModelAdmin):
    list_display = ("channel_id", "title", "invite_link", "order")


@admin.register(BotSettings)
class BotSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "admin_chat_id")

    def has_add_permission(self, request):
        return not BotSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
