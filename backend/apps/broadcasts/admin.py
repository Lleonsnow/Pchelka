from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

from .models import Broadcast, BroadcastTemplate
from .services import queue_broadcast_from_template


@admin.register(BroadcastTemplate)
class BroadcastTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "text_preview", "image_thumb", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("name", "text")
    ordering = ("order", "id")
    actions = ("action_send_now",)

    fieldsets = (
        (None, {"fields": ("name", "text", "image", "is_active", "order")}),
    )

    change_form_template = "admin/broadcasts/broadcasttemplate/change_form.html"

    @admin.display(description="Текст")
    def text_preview(self, obj: BroadcastTemplate) -> str:
        t = (obj.text or "").replace("\n", " ")
        return (t[:80] + "…") if len(t) > 80 else t

    @admin.display(description="Фото")
    def image_thumb(self, obj: BroadcastTemplate) -> str:
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="max-height:40px;max-width:60px;object-fit:cover;" />',
            obj.image.url,
        )

    @admin.action(description="📤 Отправить выбранные шаблоны сейчас")
    def action_send_now(self, request, queryset):
        count = 0
        for tpl in queryset.filter(is_active=True):
            queue_broadcast_from_template(tpl)
            count += 1
        if count:
            self.message_user(
                request,
                f"В очередь поставлено рассылок: {count}. Бот отправит в течение нескольких секунд.",
                messages.SUCCESS,
            )
        else:
            self.message_user(request, "Нет активных шаблонов в выборке.", messages.WARNING)

    def response_change(self, request, obj):
        if "_send_now" in request.POST:
            if not self.has_change_permission(request, obj):
                raise PermissionDenied
            queue_broadcast_from_template(obj)
            self.message_user(
                request,
                "Рассылка поставлена в очередь. Бот отправит подписчикам в течение нескольких секунд.",
                messages.SUCCESS,
            )
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        if "_send_now" in request.POST:
            if not self.has_add_permission(request):
                raise PermissionDenied
            queue_broadcast_from_template(obj)
            self.message_user(
                request,
                "Шаблон сохранён, рассылка поставлена в очередь.",
                messages.SUCCESS,
            )
            url = reverse("admin:broadcasts_broadcasttemplate_changelist")
            return HttpResponseRedirect(url)
        return super().response_add(request, obj, post_url_continue)


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    """История отправок (записи создаются при отправке шаблона)."""

    list_display = (
        "id",
        "status_badge",
        "text_preview",
        "delivered_count",
        "error_count",
        "created_at",
        "sent_at",
    )
    list_filter = ("status",)
    ordering = ("-created_at",)
    list_per_page = 25

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj: Broadcast):
        code = (obj.status or "").replace("_", "-")
        return format_html(
            '<span class="status-badge status-{}">{}</span>',
            code,
            obj.get_status_display(),
        )

    @admin.display(description="Текст")
    def text_preview(self, obj: Broadcast) -> str:
        t = (obj.text or "").replace("\n", " ")
        return (t[:60] + "…") if len(t) > 60 else t
