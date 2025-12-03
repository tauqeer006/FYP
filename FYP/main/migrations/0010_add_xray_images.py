# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_remove_doctor_from_patientxrayinfo'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientxrayinfo',
            name='original_image',
            field=models.ImageField(blank=True, null=True, upload_to='xray_images/original/'),
        ),
        migrations.AddField(
            model_name='patientxrayinfo',
            name='saliency_map_image',
            field=models.ImageField(blank=True, null=True, upload_to='xray_images/saliency/'),
        ),
    ]
