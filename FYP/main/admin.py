from django.contrib import admin
from .models import PatientCreatedByDoctor


@admin.register(PatientCreatedByDoctor)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('fname', 'lname', 'email','dob' , 'parents' , 'gender' , 'address' , 'email' , 'contact_number' , 'medical_history' ,  'show_on_dashboard')
    list_filter = ('show_on_dashboard',)
    actions = ['show_on_dashboard_action', 'hide_from_dashboard_action']

    @admin.action(description='Add to dashboard')
    def show_on_dashboard_action(self, request, queryset):
        queryset.update(show_on_dashboard=True)

    @admin.action(description='Remove from dashboard')
    def hide_from_dashboard_action(self, request, queryset):
        queryset.update(show_on_dashboard=False)

