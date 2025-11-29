# Migration to add missing created_at column to PatientXRayInfo

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_remove_is_staff_from_patientcreatedbydoctor'),
    ]

    operations = [
        # Add created_at to PatientXRayInfo
        migrations.AddField(
            model_name='patientxrayinfo',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
    ]
