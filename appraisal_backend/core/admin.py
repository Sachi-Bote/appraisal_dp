from django.contrib import admin
from core.models import AuditLog
from .models import (
    User,
    Department,
    FacultyProfile,
    HODProfile,
    PrincipalProfile,
    Appraisal,
    ApprovalHistory,
    AppraisalScore,
    Document,
    AuditLog,
    GeneratedPDF,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active")
    search_fields = ("username",)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "log_id",
        "username_snapshot",
        "role_snapshot",
        "action",
        "entity",
        "entity_id",
        "logged_at",
    )

    list_filter = (
        "action",
        "entity",
        "role_snapshot",
        "logged_at",
    )

    search_fields = (
        "username_snapshot",
        "entity",
        "entity_id",
    )

    readonly_fields = [field.name for field in AuditLog._meta.fields]

    ordering = ("-logged_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(GeneratedPDF)
class GeneratedPDFAdmin(admin.ModelAdmin):
    list_display = ("appraisal", "pdf_path", "generated_at")


admin.site.register(Appraisal)
admin.site.register(Department)
admin.site.register(FacultyProfile)
admin.site.register(ApprovalHistory)
admin.site.register(AppraisalScore)
admin.site.register(Document)
admin.site.register(HODProfile)
admin.site.register(PrincipalProfile)


