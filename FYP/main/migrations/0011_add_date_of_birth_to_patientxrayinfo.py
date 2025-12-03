# Generated migration - Add date_of_birth field only

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_add_xray_images'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientxrayinfo',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
    ]
