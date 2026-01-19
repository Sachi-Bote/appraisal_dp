from django.contrib import admin
from .models import (
    User,
    Department,
    FacultyProfile,
    Appraisal,
    ApprovalHistory,
    AppraisalScore,
    Document,
    AuditLog,
    GeneratedPDF,
)

admin.site.register(User)
admin.site.register(Department)
admin.site.register(FacultyProfile)
admin.site.register(Appraisal)
admin.site.register(ApprovalHistory)
admin.site.register(AppraisalScore)
admin.site.register(Document)
admin.site.register(AuditLog)
admin.site.register(GeneratedPDF)
