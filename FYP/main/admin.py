from django.contrib import admin
from .models import PatientCreatedByDoctor, PatientXRayInfo, PatientReport, User, Admin, Doctor, Patient


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'user_type', 'email', 'is_active', 'created_at')
    list_filter = ('user_type', 'is_active', 'created_at')
    search_fields = ('username', 'email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PatientCreatedByDoctor)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('fname', 'lname', 'email', 'doctor', 'gender', 'show_on_dashboard', 'is_active', 'created_at')
    list_filter = ('show_on_dashboard', 'is_active', 'gender', 'created_at')
    search_fields = ('fname', 'lname', 'email', 'contact_number')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['show_on_dashboard_action', 'hide_from_dashboard_action']

    @admin.action(description='Add to dashboard')
    def show_on_dashboard_action(self, request, queryset):
        queryset.update(show_on_dashboard=True)

    @admin.action(description='Remove from dashboard')
    def hide_from_dashboard_action(self, request, queryset):
        queryset.update(show_on_dashboard=False)


@admin.register(PatientXRayInfo)
class PatientXRayAdmin(admin.ModelAdmin):
    list_display = ('name', 'patient', 'xray_id', 'fracture_type', 'affected_hand', 'created_at')
    list_filter = ('fracture_type', 'affected_hand', 'created_at')
    search_fields = ('name', 'xray_id', 'patient__fname', 'patient__lname')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('patient',)


@admin.register(PatientReport)
class PatientReportAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'patient_idx', 'patient', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('patient_name', 'patient_idx', 'patient__fname', 'patient__lname')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('patient',)


@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'created_at')
    search_fields = ('user__username', 'department')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'created_at')
    search_fields = ('user__username', 'specialization')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Patient)
class PatientModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')

