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
    created_at = models.DateTimeField(null=True, blank=True, db_index=True)
    updated_at = models.DateTimeField(null=True, blank=True)

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
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Admins"


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Doctors"


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField()
    medical_history = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)


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
    
    # Image fields for X-ray storage
    original_image = models.ImageField(upload_to='xray_images/original/', null=True, blank=True)
    saliency_map_image = models.ImageField(upload_to='xray_images/saliency/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

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


class ExerciseSession(BaseModel):
    """Exercise session tracking for rehabilitation exercises"""
    # Patient association
    patient = models.ForeignKey(
        'PatientCreatedByDoctor',
        on_delete=models.CASCADE,
        related_name='exercise_sessions',
        db_index=True,
        null=True,
        blank=True
    )
    
    # Doctor who supervised (optional - null if patient doing it themselves)
    doctor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='supervised_exercise_sessions',
        db_index=True,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'doctor'}
    )
    
    # Exercise details
    exercise_name = models.CharField(max_length=200, db_index=True)
    exercise_date = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Performance metrics
    total_reps_completed = models.IntegerField(default=0)  # Out of 10
    correct_frames = models.IntegerField(default=0)  # Frames with correct posture
    incorrect_frames = models.IntegerField(default=0)  # Frames with incorrect posture
    total_frames = models.IntegerField(default=0)  # Total frames processed
    accuracy_percentage = models.FloatField(default=0.0)  # Overall accuracy %
    
    # Session tracking
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    session_status = models.CharField(
        max_length=20,
        choices=[
            ('completed', 'Completed'),
            ('incomplete', 'Incomplete'),
            ('stopped', 'Stopped Early'),
        ],
        default='completed'
    )
    
    # Notes/feedback
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-exercise_date']
        indexes = [
            models.Index(fields=['patient', 'exercise_date']),
            models.Index(fields=['doctor', 'exercise_date']),
            models.Index(fields=['exercise_name', 'exercise_date']),
            models.Index(fields=['session_status']),
        ]
        verbose_name_plural = "Exercise Sessions"
    
    def __str__(self):
        patient_name = f"{self.patient.fname} {self.patient.lname}" if self.patient else "Unknown"
        return f"{patient_name} - {self.exercise_name} ({self.exercise_date.strftime('%Y-%m-%d %H:%M')})"


class ExerciseMetrics(BaseModel):
    """Detailed frame-by-frame metrics for exercise sessions"""
    session = models.ForeignKey(
        ExerciseSession,
        on_delete=models.CASCADE,
        related_name='frame_metrics',
        db_index=True
    )
    
    frame_number = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Joint angles
    left_shoulder_angle = models.FloatField(null=True, blank=True)
    right_shoulder_angle = models.FloatField(null=True, blank=True)
    left_elbow_angle = models.FloatField(null=True, blank=True)
    right_elbow_angle = models.FloatField(null=True, blank=True)
    left_wrist_angle = models.FloatField(null=True, blank=True)
    right_wrist_angle = models.FloatField(null=True, blank=True)
    
    # Assessment
    is_correct = models.BooleanField(default=False)
    feedback_message = models.CharField(max_length=500, blank=True)
    confidence_score = models.FloatField(default=0.0)  # 0-1
    
    class Meta:
        ordering = ['frame_number']
        indexes = [
            models.Index(fields=['session', 'frame_number']),
        ]
    
    def __str__(self):
        return f"Frame {self.frame_number} - Session {self.session.id}"


class PatientProgressPlan(BaseModel):
    """AI-generated personalized exercise plan"""
    patient = models.ForeignKey(
        'PatientCreatedByDoctor',
        on_delete=models.CASCADE,
        related_name='progress_plans',
        db_index=True
    )
    
    doctor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'doctor'}
    )
    
    # Plan details
    injury_type = models.CharField(max_length=100)  # e.g., "Left Shoulder Fracture"
    current_week = models.IntegerField(default=1)
    total_weeks = models.IntegerField(default=6)
    
    # Plan content (stored as JSON)
    plan_json = models.JSONField(default=dict)  # {week: [exercises]}
    
    # Predictions
    predicted_recovery_date = models.DateField(null=True, blank=True)
    predicted_recovery_score = models.IntegerField(default=0)  # 0-100
    
    # Tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('paused', 'Paused'),
            ('archived', 'Archived'),
        ],
        default='active'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Plan for {self.patient.fname} - Week {self.current_week}"


class ExerciseDifficulty(BaseModel):
    """Track difficulty settings per patient per exercise"""
    patient = models.ForeignKey(
        'PatientCreatedByDoctor',
        on_delete=models.CASCADE,
        related_name='difficulty_settings',
        db_index=True
    )
    
    exercise_name = models.CharField(max_length=200, db_index=True)
    
    # Difficulty parameters
    current_level = models.IntegerField(default=1)  # 1-5
    reps_target = models.IntegerField(default=10)
    speed_modifier = models.FloatField(default=1.0)  # 0.5 = slow, 2.0 = fast
    rom_percentage = models.IntegerField(default=100)  # Range of motion 50-100%
    
    # Tracking
    last_session_accuracy = models.FloatField(default=0.0)
    consecutive_good_sessions = models.IntegerField(default=0)  # For auto-level-up
    
    class Meta:
        unique_together = ['patient', 'exercise_name']
        indexes = [
            models.Index(fields=['patient', 'exercise_name']),
        ]
    
    def __str__(self):
        return f"{self.patient.fname} - {self.exercise_name} (Level {self.current_level})"


class RecoveryPrediction(BaseModel):
    """Store recovery timeline predictions"""
    patient = models.ForeignKey(
        'PatientCreatedByDoctor',
        on_delete=models.CASCADE,
        related_name='recovery_predictions',
        db_index=True
    )
    
    # Prediction details
    predicted_days_to_recovery = models.IntegerField()
    predicted_recovery_date = models.DateField()
    confidence_percentage = models.FloatField(default=0.0)  # 0-100
    
    # Model inputs
    accuracy_at_prediction = models.FloatField()
    sessions_completed = models.IntegerField()
    days_since_injury = models.IntegerField()
    
    # Feedback
    status = models.CharField(
        max_length=20,
        choices=[
            ('on_track', 'On Track'),
            ('ahead', 'Ahead of Schedule'),
            ('behind', 'Behind Schedule'),
        ],
        default='on_track'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.fname} - Recovery in {self.predicted_days_to_recovery} days"


# Keep this for backward compatibility during migration
Patient_Report = PatientReport