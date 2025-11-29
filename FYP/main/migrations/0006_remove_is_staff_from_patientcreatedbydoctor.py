# Migration to remove is_staff column from PatientCreatedByDoctor

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_add_updated_at_to_patientcreatedbydoctor'),
    ]

    operations = [
        # Remove is_staff column from PatientCreatedByDoctor (it shouldn't be there)
        migrations.RemoveField(
            model_name='patientcreatedbydoctor',
            name='is_staff',
        ),
    ]
