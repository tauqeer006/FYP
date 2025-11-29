# Generated migration to add timestamp fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_user_email_user_reset_token_user_reset_token_created'),
    ]

    operations = [
        # Add created_at and updated_at to User model
        migrations.AddField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        
        # Add created_at and updated_at to Admin model
        migrations.AddField(
            model_name='admin',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='admin',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),
        
        # Add created_at and updated_at to Doctor model
        migrations.AddField(
            model_name='doctor',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='doctor',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),
        
        # Add created_at and updated_at to Patient model
        migrations.AddField(
            model_name='patient',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),
    ]

