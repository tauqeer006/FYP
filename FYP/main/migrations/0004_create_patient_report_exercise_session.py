# Generated migration to create missing tables

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_add_timestamps'),
    ]

    operations = [
        # Create PatientReport table
        migrations.CreateModel(
            name='PatientReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('patient_name', models.CharField(max_length=100)),
                ('patient_idx', models.CharField(db_index=True, max_length=50)),
                ('report_file', models.FileField(upload_to='reports/')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='main.patientcreatedbydoctor', db_index=True)),
            ],
            options={
                'verbose_name_plural': 'Patient Reports',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create ExerciseSession table
        migrations.CreateModel(
            name='ExerciseSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('exercise_name', models.CharField(db_index=True, max_length=200)),
                ('exercise_date', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('total_reps_completed', models.IntegerField(default=0)),
                ('correct_frames', models.IntegerField(default=0)),
                ('incorrect_frames', models.IntegerField(default=0)),
                ('total_frames', models.IntegerField(default=0)),
                ('accuracy_percentage', models.FloatField(default=0.0)),
                ('session_id', models.CharField(db_index=True, max_length=100, unique=True)),
                ('session_status', models.CharField(choices=[('completed', 'Completed'), ('incomplete', 'Incomplete'), ('stopped', 'Stopped Early')], default='completed', max_length=20)),
                ('notes', models.TextField(blank=True, null=True)),
                ('patient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exercise_sessions', to='main.patientcreatedbydoctor', db_index=True)),
                ('doctor', models.ForeignKey(blank=True, limit_choices_to={'user_type': 'doctor'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervised_exercise_sessions', to=settings.AUTH_USER_MODEL, db_index=True)),
            ],
            options={
                'verbose_name_plural': 'Exercise Sessions',
                'ordering': ['-exercise_date'],
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='patientreport',
            index=models.Index(fields=['patient', 'created_at'], name='main_patien_patient_391cb3_idx'),
        ),
        migrations.AddIndex(
            model_name='patientreport',
            index=models.Index(fields=['patient_idx'], name='main_patien_patient_171a75_idx'),
        ),
        migrations.AddIndex(
            model_name='exercisesession',
            index=models.Index(fields=['patient', 'exercise_date'], name='main_exerci_patient_5f0934_idx'),
        ),
        migrations.AddIndex(
            model_name='exercisesession',
            index=models.Index(fields=['doctor', 'exercise_date'], name='main_exerci_doctor__aa930a_idx'),
        ),
        migrations.AddIndex(
            model_name='exercisesession',
            index=models.Index(fields=['exercise_name', 'exercise_date'], name='main_exerci_exercis_f18fc0_idx'),
        ),
        migrations.AddIndex(
            model_name='exercisesession',
            index=models.Index(fields=['session_status'], name='main_exerci_session_d205bc_idx'),
        ),
    ]
