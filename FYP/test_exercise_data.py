#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FYP.settings')
django.setup()

import json
from django.contrib.auth.models import User
from main.models import ExerciseSession, PatientCreatedByDoctor

print("=== CHECKING EXERCISE SESSION DATA ===")
total_sessions = ExerciseSession.objects.count()
print(f"Total ExerciseSessions in database: {total_sessions}")

if total_sessions > 0:
    # Show recent sessions
    recent_sessions = ExerciseSession.objects.all().order_by('-exercise_date')[:5]
    for session in recent_sessions:
        patient_info = f"{session.patient.fname} {session.patient.lname}" if session.patient else "N/A"
        doctor_info = session.doctor.username if session.doctor else "N/A"
        print(f"\nSession ID: {session.session_id}")
        print(f"  Exercise: {session.exercise_name}")
        print(f"  Patient: {patient_info}")
        print(f"  Doctor: {doctor_info}")
        print(f"  Reps: {session.total_reps_completed}")
        print(f"  Accuracy: {session.accuracy_percentage}%")
        print(f"  Date: {session.exercise_date}")
else:
    print("\nNo exercise sessions found in database yet.")

# Check Patient records
print("\n\n=== CHECKING PATIENT DATA ===")
patients = PatientCreatedByDoctor.objects.all()
print(f"Total Patients: {patients.count()}")
for patient in patients[:3]:
    print(f"\nPatient: {patient.fname} {patient.lname}")
    print(f"  User: {patient.user}")
    print(f"  Doctor: {patient.doctor}")
    print(f"  Email: {patient.email}")

print("\n\n=== CHECKING USER DATA ===")
users = User.objects.all()
print(f"Total Users: {users.count()}")
for user in users[:3]:
    print(f"\nUser: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  User Type: {getattr(user, 'user_type', 'N/A')}")
