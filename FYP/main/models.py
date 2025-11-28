from django.db import models
from django.db.models import Q
from django.utils import timezone

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class BaseModel(models.Model):
    """Abstract base model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, user_type=None):
        if not username or not user_type:
            raise ValueError("Username and user type required")

        email = self.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            user_type=user_type
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, user_type='admin'):
        user = self.create_user(username, email, password, user_type)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):  
    USER_TYPES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )
    username = models.CharField(max_length=100, unique=True, db_index=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, db_index=True)
    email = models.EmailField(max_length=254, blank=True, null=True, db_index=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    
    # Password reset fields
    reset_token = models.CharField(max_length=500, blank=True, null=True)
    reset_token_created = models.DateTimeField(blank=True, null=True)
    
    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'user_type']

    objects = UserManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['user_type']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.username} ({self.user_type})"

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Admins"


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Doctors"


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField()
    medical_history = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PatientCreatedByDoctor(BaseModel):
    """Patient record created by a doctor"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='created_patients',
        limit_choices_to=Q(user_type='doctor') | Q(user_type='admin'),
        db_index=True
    )
    fname = models.CharField(max_length=100, db_index=True)
    lname = models.CharField(max_length=100)
    dob = models.DateField(blank=True, null=True)
    parents = models.CharField(max_length=100, blank=True)
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    email = models.CharField(max_length=200)
    medical_history = models.TextField(blank=True)
    
    show_on_dashboard = models.BooleanField(default=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['doctor', 'is_active']),
            models.Index(fields=['fname', 'lname']),
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]
        verbose_name_plural = "Patients Created By Doctor"

    def __str__(self):
        return f"{self.fname} {self.lname} (ID: {self.id})"


class PatientXRayInfo(BaseModel):
    """X-ray information for a patient"""
    patient = models.ForeignKey(
        'PatientCreatedByDoctor',
        on_delete=models.CASCADE,
        related_name='xray_records',
        db_index=True
    )
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    xray_id = models.CharField(max_length=50, unique=True, db_index=True)
    finding = models.TextField()
    fracture_type = models.CharField(max_length=100)
    affected_hand = models.CharField(max_length=10, choices=[('left', 'Left'), ('right', 'Right')])

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'created_at']),
            models.Index(fields=['xray_id']),
            models.Index(fields=['fracture_type']),
        ]
        verbose_name_plural = "Patient X-ray Info"

    def __str__(self):
        return f"{self.name} - {self.xray_id}"
    

class PatientReport(BaseModel):
    """Medical report for a patient"""
    patient = models.ForeignKey(
        'PatientCreatedByDoctor',
        on_delete=models.CASCADE,
        related_name='reports',
        db_index=True
    )
    patient_name = models.CharField(max_length=100)
    patient_idx = models.CharField(max_length=50, db_index=True)
    report_file = models.FileField(upload_to="reports/")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'created_at']),
            models.Index(fields=['patient_idx']),
        ]
        verbose_name_plural = "Patient Reports"

    def __str__(self):
        return f"{self.patient_name} ({self.patient_idx})"


# Keep this for backward compatibility during migration
Patient_Report = PatientReport