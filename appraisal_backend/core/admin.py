from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import identify_hasher

from .models import (
    Appraisal,
    AppraisalScore,
    ApprovalHistory,
    AuditLog,
    Department,
    Document,
    FacultyProfile,
    GeneratedPDF,
    HODProfile,
    PrincipalProfile,
    User,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "full_name", "role", "is_active", "is_staff", "must_change_password")
    list_filter = ("role", "is_active", "is_staff", "must_change_password")
    search_fields = ("username", "full_name", "email")

    def save_model(self, request, obj, form, change):
        password_value = form.cleaned_data.get("password")
        if password_value and (not change or "password" in form.changed_data):
            try:
                identify_hasher(password_value)
            except Exception:
                obj.set_password(password_value)

        if obj.role in ["FACULTY", "HOD"] and not obj.department:
            raise ValidationError("Department is required for Faculty/HOD users.")

        if obj.role in ["FACULTY", "HOD"]:
            department_name = (obj.department or "").strip()
            department = Department.objects.filter(department_name__iexact=department_name).first()
            if not department:
                raise ValidationError(
                    (
                        f"Department '{department_name}' does not exist. "
                        "Please use an existing department name."
                    )
                )
            obj.department = department.department_name

            if obj.role == "HOD":
                existing_hod_qs = HODProfile.objects.filter(department=department)
                if obj.pk:
                    existing_hod_qs = existing_hod_qs.exclude(user_id=obj.pk)
                existing_hod = existing_hod_qs.first()
                if existing_hod:
                    raise ValidationError(
                        f"Department '{department.department_name}' already has an HOD."
                    )
        else:
            department = None
            obj.department = None

        # Accounts created via admin should change password at first login.
        if not change:
            obj.must_change_password = True

        super().save_model(request, obj, form, change)

        if obj.role in ["FACULTY", "HOD"]:
            faculty_profile, _ = FacultyProfile.objects.get_or_create(user=obj)
            faculty_profile.full_name = obj.full_name or faculty_profile.full_name
            faculty_profile.designation = obj.designation or faculty_profile.designation
            faculty_profile.department = department
            faculty_profile.email = obj.email or faculty_profile.email
            faculty_profile.save()

        if obj.role == "HOD":
            hod_profile, _ = HODProfile.objects.get_or_create(user=obj, defaults={"department": department, "full_name": obj.full_name or obj.username})
            hod_profile.department = department
            hod_profile.full_name = obj.full_name or hod_profile.full_name
            hod_profile.email = obj.email or hod_profile.email
            hod_profile.mobile = obj.mobile_number or hod_profile.mobile
            hod_profile.save()

            department.hod = obj
            department.save(update_fields=["hod"])

        if obj.role == "PRINCIPAL":
            principal_profile, _ = PrincipalProfile.objects.get_or_create(user=obj, defaults={"full_name": obj.full_name or obj.username})
            principal_profile.full_name = obj.full_name or principal_profile.full_name
            principal_profile.email = obj.email or principal_profile.email
            principal_profile.mobile = obj.mobile_number or principal_profile.mobile
            principal_profile.save()


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
