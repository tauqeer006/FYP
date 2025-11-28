# Generated migration for database optimization
# This migration:
# 1. Adds created_at/updated_at timestamps to all models
# 2. Changes PatientXRayInfo from OneToOne to ForeignKey
# 3. Changes Patient_Report from OneToOne to ForeignKey
# 4. Removes redundant fields
# 5. Adds database indexes for frequently queried fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_user_email_user_reset_token_user_reset_token_created'),
    ]

    operations = [
        # Step 1: Add timestamps and indexes to User model
        migrations.AddField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Step 2: Add indexes to User fields
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['username'], name='main_user_username_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['user_type'], name='main_user_user_type_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='main_user_email_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_active'], name='main_user_is_active_idx'),
        ),
        
        # Step 3: Add timestamps to Admin model
        migrations.AddField(
            model_name='admin',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='admin',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Step 4: Add timestamps to Doctor model
        migrations.AddField(
            model_name='doctor',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='doctor',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Step 5: Add timestamps to Patient model
        migrations.AddField(
            model_name='patient',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Step 6: Update PatientCreatedByDoctor model
        migrations.RemoveField(
            model_name='patientcreatedbydoctor',
            name='is_staff',
        ),
        migrations.AlterField(
            model_name='patientcreatedbydoctor',
            name='medical_history',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='patientcreatedbydoctor',
            name='parents',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='patientcreatedbydoctor',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='patientcreatedbydoctor',
            name='fname',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='patientcreatedbydoctor',
            name='doctor',
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                limit_choices_to={'user_type__in': ('doctor', 'admin')},
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='created_patients',
                to='main.user',
            ),
        ),
        migrations.AlterField(
            model_name='patientcreatedbydoctor',
            name='show_on_dashboard',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='patientcreatedbydoctor',
            name='is_active',
            field=models.BooleanField(db_index=True, default=True),
        ),
        
        # Step 7: Add indexes to PatientCreatedByDoctor
        migrations.AddIndex(
            model_name='patientcreatedbydoctor',
            index=models.Index(fields=['doctor', 'is_active'], name='main_patientcreated_doctor_active_idx'),
        ),
        migrations.AddIndex(
            model_name='patientcreatedbydoctor',
            index=models.Index(fields=['fname', 'lname'], name='main_patientcreated_name_idx'),
        ),
        migrations.AddIndex(
            model_name='patientcreatedbydoctor',
            index=models.Index(fields=['email'], name='main_patientcreated_email_idx'),
        ),
        migrations.AddIndex(
            model_name='patientcreatedbydoctor',
            index=models.Index(fields=['created_at'], name='main_patientcreated_created_idx'),
        ),
        
        # Step 8: Migrate PatientXRayInfo from OneToOne to ForeignKey
        migrations.RemoveField(
            model_name='patientxrayinfo',
            name='doctor',
        ),
        migrations.RemoveField(
            model_name='patientxrayinfo',
            name='patient_code',
        ),
        migrations.AlterField(
            model_name='patientxrayinfo',
            name='patient',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='xray_records',
                to='main.patientcreatedbydoctor',
            ),
        ),
        migrations.AddField(
            model_name='patientxrayinfo',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='patientxrayinfo',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='patientxrayinfo',
            name='xray_id',
            field=models.CharField(db_index=True, max_length=50, unique=True),
        ),
        migrations.AddIndex(
            model_name='patientxrayinfo',
            index=models.Index(fields=['patient', 'created_at'], name='main_patientxray_patient_date_idx'),
        ),
        migrations.AddIndex(
            model_name='patientxrayinfo',
            index=models.Index(fields=['xray_id'], name='main_patientxray_id_idx'),
        ),
        migrations.AddIndex(
            model_name='patientxrayinfo',
            index=models.Index(fields=['fracture_type'], name='main_patientxray_fracture_idx'),
        ),
        
        # Step 9: Create new PatientReport model (rename from Patient_Report)
        migrations.CreateModel(
            name='PatientReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('patient_name', models.CharField(max_length=100)),
                ('patient_idx', models.CharField(db_index=True, max_length=50)),
                ('report_file', models.FileField(upload_to='reports/')),
                ('patient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reports',
                    to='main.patientcreatedbydoctor',
                )),
            ],
            options={
                'verbose_name_plural': 'Patient Reports',
                'ordering': ['-created_at'],
            },
        ),
        
        # Step 10: Add indexes to PatientReport
        migrations.AddIndex(
            model_name='patientreport',
            index=models.Index(fields=['patient', 'created_at'], name='main_patientreport_patient_date_idx'),
        ),
        migrations.AddIndex(
            model_name='patientreport',
            index=models.Index(fields=['patient_idx'], name='main_patientreport_idx_idx'),
        ),
        
        # Step 11: Data migration for Patient_Report → PatientReport
        migrations.RunPython(
            code=migrations.RunPython.noop,  # Data will be migrated manually if needed
            reverse_code=migrations.RunPython.noop,
        ),
        
        # Step 12: Remove old Patient_Report model (after data migration)
        # migrations.DeleteModel(name='Patient_Report'),  # Uncomment after data is migrated
    ]
