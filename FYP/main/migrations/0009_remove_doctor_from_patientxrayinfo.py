# Migration to remove doctor_id column from PatientXRayInfo

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_remove_patient_code_from_patientxrayinfo'),
    ]

    operations = [
        # Remove doctor_id column from PatientXRayInfo (it shouldn't be there)
        migrations.RemoveField(
            model_name='patientxrayinfo',
            name='doctor',
        ),
    ]
