from django.contrib import admin
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


admin.site.register(Appraisal)
admin.site.register(Department)
admin.site.register(FacultyProfile)
admin.site.register(ApprovalHistory)
admin.site.register(AppraisalScore)
admin.site.register(Document)
admin.site.register(AuditLog)
admin.site.register(GeneratedPDF)
admin.site.register(HODProfile)
admin.site.register(PrincipalProfile)
