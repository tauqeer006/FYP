# Migration to remove patient_code column from PatientXRayInfo

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_add_created_at_to_patientxrayinfo'),
    ]

    operations = [
        # Remove patient_code column from PatientXRayInfo (it shouldn't be there)
        migrations.RemoveField(
            model_name='patientxrayinfo',
            name='patient_code',
        ),
    ]
