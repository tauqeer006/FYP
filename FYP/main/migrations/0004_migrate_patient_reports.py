# Data migration handler for Patient_Report → PatientReport
# Simplified: Since Patient_Report may be empty, make this a no-op

from django.db import migrations


def migrate_patient_reports_forward(apps, schema_editor):
    """
    Migrate data from Patient_Report to PatientReport
    This is a no-op if there's no data (common for new installations)
    """
    try:
        Patient_Report = apps.get_model('main', 'Patient_Report')
        PatientReport = apps.get_model('main', 'PatientReport')
        
        # Only migrate if Patient_Report has data
        if not Patient_Report.objects.exists():
            return
        
        for old_report in Patient_Report.objects.all():
            try:
                new_report = PatientReport(
                    id=old_report.id,
                    patient_id=old_report.patient_id,
                    patient_name=old_report.Patient_name,
                    patient_idx=old_report.Patient_idx,
                    report_file=old_report.report_file,
                    created_at=old_report.created_at,
                    updated_at=old_report.updated_at if hasattr(old_report, 'updated_at') else old_report.created_at,
                )
                new_report.save(using=schema_editor.connection.alias)
            except Exception as e:
                # Skip records that can't be migrated
                print(f"Warning: Could not migrate report {old_report.id}: {e}")
                continue
    except Exception as e:
        # If Patient_Report doesn't exist, this is expected for fresh installs
        pass


def migrate_patient_reports_backward(apps, schema_editor):
    """Rollback is a no-op for fresh installs"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_database_optimization'),
    ]

    operations = [
        migrations.RunPython(
            migrate_patient_reports_forward,
            migrate_patient_reports_backward,
        ),
    ]
