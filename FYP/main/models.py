from django.db import models
from django.db.models import Q

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, user_type=None):
        if not username or not user_type:
            raise ValueError("Username and user type required")
        user = self.model(username=username, user_type=user_type)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, user_type='admin'):
        user = self.create_user(username, password, user_type)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):  
    USER_TYPES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
    )
    username = models.CharField(max_length=100, unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['user_type']

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.user_type})"

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField()
    medical_history = models.TextField()


class PatientCreatedByDoctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null = True,
        related_name='created_patients',
        limit_choices_to=Q(user_type='doctor') | Q(user_type='admin')
    )
    fname = models.CharField(max_length=100)
    lname = models.CharField(max_length=100)
    dob = models.DateField(blank=True, null=True)
    parents = models.CharField(max_length=100)
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    email = models.CharField(max_length=200)
    medical_history = models.CharField(max_length=500)
    
    created_at = models.DateTimeField(auto_now_add=True)
    show_on_dashboard = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.fname} {self.lname}"


class PatientXRayInfo(models.Model):
    patient = models.OneToOneField('PatientCreatedByDoctor', on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="xray_records" , default=1)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    patient_code = models.CharField(max_length=50)
    xray_id = models.CharField(max_length=50)
    finding = models.TextField()
    fracture_type = models.CharField(max_length=100)
    affected_hand = models.CharField(max_length=10, choices=[('left', 'Left'), ('right', 'Right')])
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.xray_id}"
    

class Patient_Report(models.Model):
    patient = models.OneToOneField('PatientCreatedByDoctor', on_delete=models.CASCADE , null=True)
    Patient_name = models.CharField(max_length=100)
    Patient_idx   = models.CharField(max_length=50)
    report_file = models.FileField(upload_to="reports/")
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.Patient_name} ({self.Patient_idx})"