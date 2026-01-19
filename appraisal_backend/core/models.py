from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    ROLE_CHOICES = (
        ('FACULTY', 'Faculty'),
        ('HOD', 'HOD'),
        ('PRINCIPAL', 'Principal'),
    )

    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.TextField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'users'

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.username} ({self.role})"



class Department(models.Model):
    department_id = models.AutoField(primary_key=True)
    department_name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'departments'

    def __str__(self):
        return self.department_name


class FacultyProfile(models.Model):
    faculty_id = models.AutoField(primary_key=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        db_column='user_id'
    )

    department = models.ForeignKey(
         Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    full_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=50, null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)

    class Meta:
        db_table = 'faculty_profiles'

    def __str__(self):
        return self.full_name


class Appraisal(models.Model):
    FORM_TYPE_CHOICES = (
        ('SPPU', 'SPPU'),
        ('PBAS', 'PBAS'),
    )

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('HOD_APPROVED', 'HOD Approved'),
        ('PRINCIPAL_APPROVED', 'Principal Approved'),
        ('LOCKED', 'Locked'),
    )

    appraisal_id = models.AutoField(primary_key=True)

    faculty = models.ForeignKey(
        FacultyProfile,
        on_delete=models.CASCADE,
        db_column='faculty_id'
    )

    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES)
    academic_year = models.CharField(max_length=20)
    semester = models.CharField(max_length=10)
    appraisal_data = models.JSONField()

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'appraisals'
        unique_together = (
            'faculty',
            'academic_year',
            'semester',
            'form_type',
        )

    def __str__(self):
        return f"{self.faculty} | {self.academic_year} | {self.form_type}"


class ApprovalHistory(models.Model):
    ACTION_CHOICES = (
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SENT_BACK', 'Sent Back'),
    )

    ROLE_CHOICES = (
        ('HOD', 'HOD'),
        ('PRINCIPAL', 'Principal'),
    )

    approval_id = models.AutoField(primary_key=True)

    appraisal = models.ForeignKey(
        Appraisal,
        on_delete=models.CASCADE,
        db_column='appraisal_id'
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='approved_by'
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    remarks = models.TextField(null=True, blank=True)
    action_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'approval_history'
        unique_together = ('appraisal', 'role')

    def __str__(self):
        return f"{self.role} - {self.action}"


class AppraisalScore(models.Model):
    score_id = models.AutoField(primary_key=True)

    appraisal = models.OneToOneField(
        Appraisal,
        on_delete=models.CASCADE,
        db_column='appraisal_id'
    )

    teaching_score = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    research_score = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    activity_score = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    feedback_score = models.DecimalField(max_digits=6, decimal_places=2, null=True)

    total_score = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    calculated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'appraisal_scores'


class Document(models.Model):
    document_id = models.AutoField(primary_key=True)

    appraisal = models.ForeignKey(
        Appraisal,
        on_delete=models.CASCADE,
        db_column='appraisal_id'
    )

    document_type = models.CharField(max_length=50, null=True, blank=True)
    file_path = models.TextField()

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='uploaded_by'
    )

    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'documents'
        unique_together = ('appraisal', 'document_type', 'file_path')


class AuditLog(models.Model):
    log_id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='user_id'
    )

    action = models.TextField()
    entity = models.CharField(max_length=50)
    entity_id = models.IntegerField()
    logged_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'audit_logs'


class GeneratedPDF(models.Model):
    pdf_id = models.AutoField(primary_key=True)

    appraisal = models.ForeignKey(
        Appraisal,
        on_delete=models.CASCADE,
        db_column='appraisal_id'
    )

    pdf_path = models.TextField()
    generated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'generated_pdfs'
