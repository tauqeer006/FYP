# Migration to add missing updated_at column to PatientCreatedByDoctor

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_create_patient_report_exercise_session'),
    ]

    operations = [
        # Add updated_at to PatientCreatedByDoctor
        migrations.AddField(
            model_name='patientcreatedbydoctor',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
