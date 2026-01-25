from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, role=None, department=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")

        user = self.model(
            username=username,
            role=role,
            department=department.department_name if department else None,
            is_active=True,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)   # ✅ SAVE FIRST

        if role == "FACULTY":
            FacultyProfile.objects.create(
                user=user,
                department=department,
            )

        elif role == "HOD":
            # 1️⃣ Create FacultyProfile FIRST
            faculty = FacultyProfile.objects.create(
                user=user,
                department=department
            )

            # 2️⃣ Create HODProfile
            HODProfile.objects.create(
                user=user,
                department=department
            )

            # 3️⃣ Sync department
            department.hod = user
            department.save()

                    # ✅ KEEP Department.hod IN SYNC

        elif role == "PRINCIPAL":
            PrincipalProfile.objects.create(user=user)

        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, password, **extra_fields)



class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("FACULTY", "Faculty"),
        ("HOD", "HOD"),
        ("PRINCIPAL", "Principal"),
        ("ADMIN", "Admin"),
    )

    username = models.CharField(max_length=150, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  # 👈 ADD THIS

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.username} ({self.role})"


class Department(models.Model):
    department_id = models.AutoField(primary_key=True)
    department_name = models.CharField(max_length=100, unique=True)

    # ✅ ADD THIS
    hod = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_departments"
    )

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
        if self.full_name:
            return self.full_name
        return self.user.username

class HODProfile(models.Model):
    hod_id = models.AutoField(primary_key=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        db_column='user_id'
    )

    department = models.OneToOneField(
        Department,
        on_delete=models.PROTECT,
        related_name="hod_profile"
    )

    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)

    class Meta:
        db_table = 'hod_profiles'
        

    def __str__(self):
        return f"HOD - {self.full_name} ({self.department})"

class PrincipalProfile(models.Model):
    principal_id = models.AutoField(primary_key=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        db_column='user_id'
    )

    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)

    class Meta:
        db_table = 'principal_profiles'

    def __str__(self):
        return f"Principal - {self.full_name}"


class Appraisal(models.Model):
    FORM_TYPE_CHOICES = (
        ('SPPU', 'SPPU'),
        ('PBAS', 'PBAS'),
    )

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('REVIEWD_BY_HOD', 'Reviewed by HOD'),
        ('RETURNED_BY_HOD', 'Returned by HOD'),
        ('HOD_APPROVED', 'HOD Approved'),
        ('REVIEWD_BY_PRINCIPAL', 'Reviewed by Principal'),
        ('RETURNED_BY_PRINCIPAL', 'Returned by Principal'),
        ('PRINCIPAL_APPROVED', 'Principal Approved'),
        ('LOCKED', 'Locked'),
    )

    appraisal_id = models.AutoField(primary_key=True)

    faculty = models.ForeignKey(
        FacultyProfile,
        on_delete=models.CASCADE,
        db_column='faculty_id'
    )

    # 👇 NEW (for workflow tracking)
    hod = models.ForeignKey(
        'core.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='hod_appraisals'
    )

    principal = models.ForeignKey(
        'core.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='principal_appraisals'
    )

    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES)
    academic_year = models.CharField(max_length=20)
    semester = models.CharField(max_length=10)
    is_hod_appraisal = models.BooleanField(default=False)
    appraisal_data = models.JSONField()

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    # 👇 NEW (for return / correction comments)
    remarks = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appraisals'
        unique_together = (
            'faculty',
            'academic_year',
            'semester',
            'form_type',
        )

    def __str__(self):
        return f"{self.academic_year} | {self.semester} | {self.form_type} | {self.faculty}"




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
        "Appraisal",          # ✅ STRING reference
        on_delete=models.CASCADE,
        db_column='appraisal_id',
        related_name='approval_history'
    )

    approved_by = models.ForeignKey(
        "User",               # ✅ STRING reference
        on_delete=models.PROTECT,
        db_column='approved_by',
        related_name='approvals_done'
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)

    from_state = models.CharField(max_length=50)
    to_state = models.CharField(max_length=50)

    remarks = models.TextField(null=True, blank=True)
    action_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'approval_history'
        unique_together = ('appraisal', 'role')

    def __str__(self):
        return f"{self.appraisal_id} | {self.role} | {self.action}"


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

    def __str__(self):
        return f"{self.appraisal} | Total Score: {self.total_score}"



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

    def __str__(self):
        return f"{self.document_type} | {self.appraisal}"




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

    def __str__(self):
        return f"{self.user} | {self.action} | {self.entity} ({self.entity_id})"


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

    def __str__(self):
        return f"PDF | {self.appraisal}"