from django.shortcuts import render , redirect , HttpResponse, get_object_or_404, redirect
from django.contrib.auth import get_user_model , login
from django.contrib.auth import authenticate,login as auth_login , logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponseForbidden,JsonResponse
from .models import PatientCreatedByDoctor,PatientXRayInfo,Doctor,Patient_Report
from datetime import date
from datetime import datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
import requests
import markdown
import logging
import json
import matplotlib.pyplot as plt
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
import uuid
import io
import urllib, base64
from datetime import datetime
from django.core.files.base import ContentFile
from io import BytesIO
from .models import Patient_Report
### the new data for mediapipe working:

from django.shortcuts import render
from django.http import JsonResponse
import cv2, numpy as np, base64
from io import BytesIO
from PIL import Image
from collections import deque
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import mediapipe as mp

logging.basicConfig(level=logging.INFO)

User = get_user_model()

# this is login  of doctor
def login_doctor(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")


        print("Username:", username)
        print("Password:", password)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            print("Authenticated:", user)
            if user.user_type == 'doctor': 
                login(request, user)
                return redirect('diagnosis_page')  

            else:
                return HttpResponse("Not a doctor")
        else:
            print("Authentication failed")
            return HttpResponse("Wrong password or username")

    return render(request, "doctor_login.html")

def signup(request):
    if request.method == "POST":
       username = request.POST.get("username")
       password = request.POST.get("password")
       email = request.POST.get("email")
       user = User.objects.create_user(username ,  password , "doctor")
       print("user account created with:" , username , "password" , password)
       user.save()
       return redirect("loginSystem")
    return render(request , "signup.html")

def MainPage(request):
    """Landing page with appointment form submission."""
    departments = [
        "Orthopedics & Trauma",
        "Radiology & Imaging",
        "Sports Medicine",
        "Physical Therapy & Rehab",
        "AI Diagnostic Lab",
    ]
    doctor_records = Doctor.objects.select_related('user').order_by('user__username')
    doctor_options = []

    if doctor_records.exists():
        for doctor in doctor_records:
            doc_name = doctor.user.username
            label = doc_name.title()
            if doctor.specialization:
                label = f"{label} - {doctor.specialization}"
            doctor_options.append({
                "value": doc_name,
                "label": label,
            })
    else:
        fallback_users = User.objects.filter(user_type='doctor').order_by('username')
        for user in fallback_users:
            doctor_options.append({
                "value": user.username,
                "label": user.username.title(),
            })
    form_success = None
    form_error = None
    form_data = {}

    if request.method == "POST":
        form_data = {
            "name": request.POST.get("name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "department": request.POST.get("department", "").strip(),
            "doctor": request.POST.get("doctor", "").strip(),
            "appointment_date": request.POST.get("appointment_date", "").strip(),
            "message": request.POST.get("message", "").strip(),
        }

        if not all(form_data.values()):
            form_error = "Please fill in every field before submitting."
        else:
            subject = f"New Appointment Request from {form_data['name']}"
            email_message = (
                f"New appointment inquiry from the website:\n\n"
                f"Name: {form_data['name']}\n"
                f"Email: {form_data['email']}\n"
                f"Phone: {form_data['phone']}\n"
                f"Preferred Department: {form_data['department']}\n"
                f"Preferred Doctor: {form_data['doctor']}\n"
                f"Preferred Date: {form_data['appointment_date']}\n"
                f"Message:\n{form_data['message']}\n"
            )
            try:
                send_mail(
                    subject,
                    email_message,
                    getattr(settings, "DEFAULT_FROM_EMAIL", "tauqeerqureshi112@gmail.com"),
                    ['tauqeerqureshi112@gmail.com'],
                    fail_silently=False,
                )
                form_success = "Thanks! Your request was sent. We'll reach out shortly."
                form_data = {}
            except Exception:
                form_error = "Unable to send your request right now. Please try again in a few minutes."

    context = {
        "departments": departments,
        "doctor_options": doctor_options,
        "form_success": form_success,
        "form_error": form_error,
        "form_data": form_data,
    }
    return render(request, "index.html", context)

@never_cache
@login_required(login_url='admin_login')
def dashboard(request):
    try:
        user = request.user
        print(f"Dashboard accessed by: {user} with user_type: {getattr(user, 'user_type', None)}")
        if hasattr(user, 'user_type') and user.user_type == 'admin':
            # Calculate statistics
            all_users = User.objects.all()
            total_users = all_users.count()
            total_doctors = all_users.filter(user_type='doctor').count()
            total_patients = PatientCreatedByDoctor.objects.all().count()
            total_reports = Patient_Report.objects.all().count()
            
            # Get recent activity from Patient_Report
            recent_activity = Patient_Report.objects.all().order_by('-created_at')[:5]
            
            return render(request, "index_admin.html", {
                'total_users': total_users,
                'total_doctors': total_doctors,
                'total_patients': total_patients,
                'total_reports': total_reports,
                'recent_activity': recent_activity,
                'last_login': user.last_login,
            })
        else:
            return HttpResponseForbidden("Access Denied: Admins only.")
        
    except Exception as e:
        return HttpResponse(e)

def logoutpage(request):
    logout(request)
    return redirect("admin_login")


def admin_login1(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        print(username, password)
        if user is not None and hasattr(user, 'user_type') and user.user_type == 'admin':
            
            auth_login(request, user)
            return redirect('index_admin' )
        else:
            messages.error(request, 'Access denied: Not an admin user or invalid credentials.')
            return render(request, 'Admin1/admin_login.html')
    return render(request, 'Admin1/admin_login.html')


def patient_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        print(username, password)
        if user is not None and hasattr(user, 'user_type') and user.user_type == 'patient':      

            auth_login(request, user)
            return redirect('patient_dashboard' )
        
        else:
            logging.info("Entering the incorrect things")
            messages.error(request, 'Access denied: Not an patient user or invalid credentials.')
            return render(request , "patient/patient_login.html")
        



    return render(request , "patient/patient_login.html")

@never_cache
@login_required(login_url='patient_logins')
def patient_dashboard(request):
    try:
        patients = get_object_or_404(
            PatientCreatedByDoctor,
            user=request.user,
            show_on_dashboard=True
        )
        data = patients.user.username
        print("the name of patient is:" , data,".")

        account_created = patients.created_at

        print("This account created at:" , account_created)


        doctor_link = patients.doctor
        print("the doctor linkage is:" , doctor_link)

        ### left with the file of doctor:
        
        reports = Patient_Report.objects.filter(patient=patients)

        for report in reports:
            print("Patient Name:", report.Patient_name)
            print("Patient ID:", report.Patient_idx)
            print("Report File URL:", report.report_file.url)   
            print("Report File Path:", report.report_file.path) 

        doctor = patients.doctor
        xray_info = PatientXRayInfo.objects.filter(patient=patients).first()
        total_reports = reports.count()
        reports = reports.order_by('-created_at')

        age_years = None
        if patients.dob:
            today = date.today()
            age_years = today.year - patients.dob.year - (
                (today.month, today.day) < (patients.dob.month, patients.dob.day)
            )

        context = {
            "patients": patients,
            "doctor": doctor,
            "age": age_years,
            "reports": reports,
            "total_reports": total_reports,
            "xray_info": xray_info,
            "fracture_type": xray_info.fracture_type if xray_info else None,
            "now": timezone.now(),
        }

        return render(request, "patient/patient_dashboard.html", context)


    
    except Exception as e:
        return HttpResponse(str(e))
    
@never_cache
@login_required(login_url='patient_logins')    
def user_profile(request):
    try:
        user = request.user
        
        # Check if user is a doctor
        if user.user_type == 'doctor':
            try:
                doctor_profile = Doctor.objects.get(user=user)
            except Doctor.DoesNotExist:
                doctor_profile = None
            
            # Get doctor's patients
            doctor_patients = PatientCreatedByDoctor.objects.filter(doctor=user)
            
            context = {
                "user": user,
                "doctor_profile": doctor_profile,
                "doctor_patients": doctor_patients,
                "user_type": "doctor",
                "patients": None,
                "reports": []
            }
            return render(request, "patient/user/edit_user.html", context)
        
        # For patients - get their profile data
        patients = None
        patients1 = None
        reports = []
        
        # Try different ways to find the patient
        try:
            # First try: get by user and show_on_dashboard
            patients = PatientCreatedByDoctor.objects.get(user=request.user, show_on_dashboard=True)
        except PatientCreatedByDoctor.DoesNotExist:
            try:
                # Second try: get by user only
                patients = PatientCreatedByDoctor.objects.get(user=request.user)
            except PatientCreatedByDoctor.DoesNotExist:
                # Third try: get first patient if any exist
                all_patients = PatientCreatedByDoctor.objects.filter(user=request.user)
                if all_patients.exists():
                    patients = all_patients.first()
                else:
                    # If still no patient, try to get any patient from database
                    all_patients = PatientCreatedByDoctor.objects.all()
                    if all_patients.exists():
                        patients = all_patients.first()
        
        if patients:
            data = patients.user.username
            print("the name of patient is:" , data,".")

            account_created = patients.created_at
            print("This account created at:" , account_created)

            doctor_link = patients.doctor
            print("the doctor linkage is:" , doctor_link)

            # Get X-ray info if exists
            try:
                patients1 = PatientXRayInfo.objects.get(patient=patients)
            except PatientXRayInfo.DoesNotExist:
                patients1 = None
                
            reports = Patient_Report.objects.filter(patient=patients)

            if patients1:
                print("the data getting from the patients are:" , patients1)
                print("final conclusion from patient x ray is:" , patients1.name)

            for report in reports:
                print("Patient Name:", report.Patient_name)
                print("Patient ID:", report.Patient_idx)
                if report.report_file:
                    print("Report File URL:", report.report_file.url)   
                    print("Report File Path:", report.report_file.path)

            context = {"reports": reports, "patients": patients1, "user_type": "patient"}
            return render(request, "patient/user/edit_user.html", context)
        else:
            # No patient found in database
            return render(request, "patient/user/edit_user.html", {
                "error": "Your patient profile is not set up yet. Please contact your doctor.",
                "reports": [],
                "patients": None,
                "user_type": "patient"
            })
        
    except Exception as e:
        print(f"Error in user_profile: {str(e)}")
        return render(request, "patient/user/edit_user.html", {
            "error": f"Error loading profile: {str(e)}",
            "reports": [],
            "patients": None
        })
@never_cache
@login_required(login_url='patient_logins')      
def user_report(request):
    try:
        
            return redirect("http://127.0.0.1:5003")
        
    except Exception as e:
        return HttpResponse(str(e), status=500)
@never_cache
@login_required(login_url='patient_logins')      
def detailed_history(request):
    try:
        if request.method == "POST":
            return render(request , "patient/report/recording_pred.html")
        
    except Exception as e:
        return HttpResponse(str(e), status=500)
    
def patient_logout(request):
    logout(request)
    return redirect("patient_logins")

@never_cache
@login_required(login_url='admin_login')
def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password1')
        email    = request.POST.get("emails")
        ages   = request.POST.get("ages")
        gender = request.POST.get("genders")
        phone = request.POST.get("phno")
        roles = request.POST.get('roles')
        print("the gender i am getting is:" , gender , "roles is:" , roles)
        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'add_user.html')
        if roles and roles.lower() == 'doctor':

            user = User.objects.create_user(username=username, password=password, user_type='doctor')
            user.user_type = 'doctor'  
            user.save()
            print("Doctor account has been created with username:", username , "password:" , password)
            subject = "Your Account Details"
            message = f"""
            Hello {username},

            Your doctor account has been created successfully.
            Username: {username}
            Password: {password}

            You can now log in to the system.
            """
            from_email = 'tauqeerqureshi112@gmail.com'
            recipient_list = [email]

            send_mail(subject, message, from_email, recipient_list)

            
        
## new data changes doing:
        if roles and roles.lower() == 'patient':
            auth_user = User.objects.create_user(
                    username=username,
                    password=password,  
                     user_type='patient' )  
            auth_user.user_type = 'patient'  
            auth_user.save()      
                    
                                               
            first_name = username
            last_name = username
            dob = "2025-6-6"
            parents = "ali"
            genders = gender
            address = "idk"
            email  = email
            medical_history = "working fine"

            user = PatientCreatedByDoctor.objects.create(
                                                        user=auth_user,
                                                        doctor=request.user if request.user.user_type == 'doctor' else  None,
                                                        fname= first_name
                                                        ,lname= last_name,
                                                        dob   = dob,
                                                        parents= parents,
                                                         gender = genders,
                                                          address = address,
                                                           contact_number = phone,
                                                            email = email ,
                                                             medical_history = medical_history )
            user.save()
            print("patient account has been created with username:", username , "password:" , password)
            messages.success(request, "patient user created successfully.")
            subject = "Your Account Details"
            message = f"""
            Hello {username},

            Your Patient account has been created successfully.
            Username: {username}
            Password: {password}

            You can now log in to the system.
            """
            from_email = 'tauqeerqureshi112@gmail.com'
            recipient_list = [email]

            send_mail(subject, message, from_email, recipient_list)   

        else:
            messages.error(request, "Role not recognized or not handled.")
    return render(request, 'index_admin.html')

@never_cache
@login_required(login_url='admin_login')
def manage_user(request):

    visible_patients = PatientCreatedByDoctor.objects.filter(show_on_dashboard=True)

    pending_patients = PatientCreatedByDoctor.objects.filter(show_on_dashboard=False)

    Doctor_data = User.objects.all().values("id", "username", "doctor")
    doctor = [i for i in Doctor_data]

    # Calculate statistics
    all_users = User.objects.all()
    total_users = all_users.count()
    total_doctors = all_users.filter(user_type='doctor').count()
    total_patients = PatientCreatedByDoctor.objects.all().count()
    active_users = all_users.filter(is_active=True).count()
    inactive_users = total_users - active_users
    
    # Calculate percentages
    doctor_percentage = round((total_doctors / total_users * 100)) if total_users > 0 else 0
    patient_percentage = round((total_patients / total_users * 100)) if total_users > 0 else 0

    return render(request, 'manage_user.html', {
        'visible_patients': visible_patients,
        'pending_patients': pending_patients,
        "doctor" : doctor,
        'total_users': total_users,
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'doctor_percentage': doctor_percentage,
        'patient_percentage': patient_percentage,
        'users': all_users,  # Add all users to context for displaying in table
    })

def remove_doctor(request , doctor_id):
    print("i am in remove doctor fun:")

    doctor_data = User.objects.filter( id=doctor_id, user_type='doctor')
    doctor_data.delete()
    return redirect("manageuser")



def toggle_dashboard_status(request, patient_id):
    patient = get_object_or_404(PatientCreatedByDoctor, id=patient_id)
    
    patient.delete()
    return redirect('manageuser')

def total_patient_graphs(request):
    patients = PatientCreatedByDoctor.objects.all()
    doctors = User.objects.filter( user_type='doctor')

    patients_data = len([i for i in patients])
    doctors_data = len([i for i in doctors])

    plt.switch_backend('AGG')
    plt.figure(figsize=(5, 4))

    labels = ["patients" , "doctors"]
    values = [patients_data , doctors_data]
    plt.bar(labels , values)
    plt.title("total number of patients and doctors")
    plt.xlabel("categories")
    plt.ylabel("counts")

    buf =io.ByteIO()
    plt.savefig(buf , format = 'png')
    buf.seek(0)
    graph = base64.b64encode(buf.getvalue()).decode("utf-8")

    return render(request, "index_admin.html", {"graph": graph})


@login_required
@never_cache
def diagnosis(request):
    # Get doctor's patients
    total_patient = PatientCreatedByDoctor.objects.filter(doctor=request.user).count()
    all_patients = PatientXRayInfo.objects.filter(doctor=request.user)
    for i in all_patients:
        print("my patient is:" , i)
    logging.info("The total number of patients are")
    logging.info(total_patient)
    
    # Calculate statistics for doctor dashboard
    total_xray_records = PatientXRayInfo.objects.filter(doctor=request.user).count()
    total_reports = Patient_Report.objects.filter(patient__doctor=request.user).count()
    recent_analysis_count = Patient_Report.objects.filter(patient__doctor=request.user).count()
    recent_patients = PatientCreatedByDoctor.objects.filter(doctor=request.user).order_by('-created_at')[:5]
    
    context = {
        'total_doctor_patients': total_patient,
        'total_xray_records': total_xray_records,
        'total_reports': total_reports,
        'recent_analysis_count': recent_analysis_count,
        'recent_patients': recent_patients,
        'data': PatientCreatedByDoctor.objects.all().order_by('-id')[:3]
    }
    
    return render(request, "Doctor/doctor_dashboard.html", context)


def add_patient(request):
    
    if request.method == 'POST':
        if not request.user.is_authenticated or request.user.user_type != 'doctor':
            return JsonResponse({"error": "Unauthorized access"}, status=403)
        fname = request.POST.get('fname')
        password = request.POST.get("lname")
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        parents = request.POST.get('parents')
        contact_number = request.POST.get('contact_number')
        email = request.POST.get('email')
        address = request.POST.get('address')
        medical_history = request.POST.get('medical_history')
        date_right_now = datetime.now().date()
        conversion = datetime.strptime(dob, "%Y-%m-%d").date()
        logging.info("The given datetime from the dataset i found is:")
        logging.info(conversion)
        if date_right_now < conversion:
            logging.info("I am inside the condition")

            messages.error(request, "Date of Birth cannot be in the future.")
            return render(request, "Doctor/Patient/add_patient.html", { "dob": dob})
        

        user = User.objects.create_user(
                    username=fname,
                    password=password,  
                     user_type='patient' )  
        user.user_type = 'patient'  
        user.save()   
        
        PatientCreatedByDoctor.objects.create(
            user=user,
            doctor=request.user if request.user.user_type == 'doctor' else None,
            fname = fname ,
            lname = password,
            dob = dob,
            gender = gender,
            parents = parents,
            contact_number = contact_number  ,
            email = email ,
            address = address,
            medical_history = medical_history,

        )
        print("Storing data to the database here:")
        return render(request , "Doctor/Patient/add_patient.html")

    return render(request , 'Doctor/Patient/add_patient.html')




def get_all_patients_json(request):
    patients = PatientCreatedByDoctor.objects.all()
    data = []

    for patient in patients:
        data.append({
            'full_name': f"{patient.fname} {patient.lname}",
            'dob': patient.dob,
            'gender': patient.get_gender_display(),
            'parents': patient.parents,
            'contact_number': patient.contact_number,
            'email': patient.email,
            'address': patient.address,
            'medical_history': patient.medical_history,
            'created_at': patient.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    response = {
        'total_patients': patients.count(),
        'patients': data,
    }

    return JsonResponse(response)


def calculate_age(dob):
    if dob:
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return ''

def get_all_patients(request):
    patients = PatientCreatedByDoctor.objects.all()

    print("Patients from DB:", patients)
    for p in patients:
        p.age = calculate_age(p.dob)
    return render(request, 'Doctor/Patient/all_patients.html', {'patients': patients})


      
   
@csrf_protect
def predict_diagnosis(request):
    patients = PatientCreatedByDoctor.objects.all()

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient_id')
            patient = PatientCreatedByDoctor.objects.get(id=patient_id)
            images = request.FILES.getlist('xray_images')
            logging.info("I get the detail of patient:")
            logging.info(patient)

            if not images:
                return render(request, 'Doctor/Patient/diagnosis_form.html', {
                    'patients': patients,
                    'error': 'No image uploaded'
                })

            image = images[0]  

            # ---------------------- Flask API 1: Fracture Detection ----------------------
            flask_url1 = 'http://xray-api:5002/detect-fracture'
            response1 = requests.post(flask_url1, files={'image': image})
            fracture_data = response1.json()
            print("the data from the yolo model is:" , fracture_data)

            # ---------------------- Flask API 2: Left/Right Prediction ----------------------
            image.seek(0) 
            flask_url2 = 'http://cnn-api:5001/predict-lr'
            response2 = requests.post(flask_url2, files={'image': image})
            lr_data = response2.json()
            print("the data from the left right model is:" , lr_data)

            prediction_result = {
                'patient_name': f"{patient.fname} {patient.lname}",
                'patient_age': calculate_age(patient.dob),
                'patient_id': patient.id,
                'xray_id': f"XRAY-{datetime.now().timestamp()}",
                'fracture_types': fracture_data.get('fracture_types', ['No fracture detected']),
                'left_right': lr_data.get('prediction', 'Unknown'),
                'confidence': 0.95,  # Placeholder
                'findings': "AI-based fracture and side analysis completed."
            }
            print("I am creating my x ray data")
            xray_info, created = PatientXRayInfo.objects.update_or_create(
            patient=patient,  
            defaults={
                "doctor": request.user,
                'name': prediction_result['patient_name'],
                'age': prediction_result['patient_age'],
                'patient_code': prediction_result['patient_id'],
                'xray_id': prediction_result['xray_id'],
                'finding': prediction_result['findings'],
                'fracture_type': prediction_result['fracture_types'][0],  
                'affected_hand': prediction_result['left_right'],
            }
)
            print("This is my database x ray info i am sending----------------" , xray_info ,"created values:" ,  created)
            

            return render(request, 'Doctor/prediction_result.html', {
                'patients': patients,
                'prediction_result': prediction_result
            })

        except Exception as e:
            return render(request, 'Doctor/Patient/diagnosis_form.html', {
                'patients': patients,
                'error': str(e)
            })

    return render(request, 'Doctor/Patient/diagnosis_form.html', {
        'patients': patients
    })

### check patient data is it saving or not:
def patients_data(request):
    try:
        from django.forms.models import model_to_dict

        data = PatientXRayInfo.objects.all()
        datas = [model_to_dict(i) for i in data]
        return JsonResponse(datas , safe=False)
    
    except Exception as e:
        return {"issues": str(e)}

def Report(request):
    try:
        summary = ""
        recommendation = ""
        
        latest_report = PatientXRayInfo.objects.latest('updated_at')
        logging.info("The latest report is:")
        logging.info(latest_report)
        doctor_data = PatientXRayInfo.objects.latest('updated_at').doctor
        print("the doctor id is:" , doctor_data)

        
        
        
        prompt1 = f"""
You are an orthopedic diagnostic AI. Generate a structured *Medical Diagnostic Report* for a pediatric fracture case.

STRICT RULES:
- Do NOT write any patient details in the report.
- Use ONLY the clinical data below for medical reasoning.
- Follow the EXACT OUTPUT format given.
- Do NOT add extra sections.
- Keep the diagnosis short (3–4 lines).
- Explain only:
  • How this type of fracture typically occurs  
  • Expected healing time (in weeks)  
  • Brief medical explanation (no patient history)

CLINICAL DATA:
- Affected Hand: {latest_report.affected_hand}
- Fracture Type: {latest_report.fracture_type}
- Finding: {latest_report.finding}

---------------------------------------------------------
OUTPUT FORMAT (MANDATORY):

### 🩺 Medical Diagnosis
(Write 3–4 lines about how this type of fracture occurs + healing duration)

### Recommended Exercises
(Choose 5–8 exercises based only on fracture severity)

For each exercise include:
1. **Exercise Name**
2. One-line description
3. One safety tip

Use the following approved exercise list ONLY:

Pendulum Swing
Active Shoulder Flexion (Wall Slide)
Shoulder Abduction (Assisted)
External Rotation with Band
Internal Rotation with Band
Scapular Retraction/Depression (Wall Slide)
Prone Y Raise
Wall Angel
Seated Shoulder Flexion (Assisted)
Side-lying External Rotation
Isometric Shoulder Flexion
Scaption
External Rotation in 90° Abduction
Shoulder Horizontal Abduction (Prone)
Shoulder Extension (Assisted)
Chair Push-Up (Mini)
I-Y-T Raise
Serratus Punch
Shoulder Flexion in Side-lying
Arm Across Chest Stretch
Assisted Overhead Reach
Gentle Shoulder Abduction (Side-lying)
Wall Walks (Finger Walks Up Wall)

Make sure your output is fully structured with headings.
"""

        api_key = "AIzaSyB7fwNrYMa4T05ilokA3YQwjasZcwYRG5Y"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        headers = {
            'Content-Type': 'application/json',
        }

        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt1}
                    ]
                }
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        generated_report = result['candidates'][0]['content']['parts'][0]['text']
        #logging.info(generated_report)
        ## end of report 1.

        """generating table:"""
        test_results = []

        
        fracture = latest_report.fracture_type.lower()
        hand = latest_report.affected_hand.lower()

        hand_prefix = f"{hand.capitalize()} hand -"

        if "boneanomaly" in fracture:
           test_results = [
            {"test": f"X-ray {hand.capitalize()} Wrist", "result": f"{hand_prefix} Structural irregularity observed", "remarks": "Orthopedic follow-up needed"},
            {"test": "MRI", "result": "Localized bone density variations", "remarks": "Consider further metabolic evaluation"},
            {"test": "Blood Work", "result": "Elevated alkaline phosphatase", "remarks": "Check for bone growth disorders"}
        ]

        elif "bonelesion" in fracture:
           test_results = [
            {"test": f"X-ray {hand.capitalize()} Hand", "result": f"{hand_prefix} Suspicious radiolucent lesion", "remarks": "Biopsy recommended"},
            {"test": "MRI", "result": "Soft tissue involvement detected", "remarks": "Needs oncology consult"},
            {"test": "CBC", "result": "Mild leukocytosis", "remarks": "Possible infection or inflammation"}
        ]

        elif "foreignbody" in fracture:
            test_results = [
            {"test": f"X-ray {hand.capitalize()} Palm", "result": f"{hand_prefix} Metallic object detected", "remarks": "Surgical removal advised"},
            {"test": "Ultrasound", "result": "No surrounding infection", "remarks": "Clean embedded object"},
            {"test": "Tetanus Profile", "result": "Booster required", "remarks": "Vaccination advised"}
        ]

        elif "fracture" in fracture:
           test_results = [
            {"test": f"X-ray {hand.capitalize()} Radius/Ulna", "result": f"{hand_prefix} Non-displaced transverse fracture", "remarks": "Casting for 6 weeks"},
            {"test": "Orthopedic Assessment", "result": "Fracture stable", "remarks": "Non-surgical management"},
            {"test": "Follow-up X-ray", "result": "Healing observed", "remarks": "Continue immobilization"}
        ]

        elif "metal" in fracture:
           test_results = [
            {"test": f"X-ray {hand.capitalize()} Arm", "result": f"{hand_prefix} Pre-existing metallic implant", "remarks": "Post-surgical monitoring"},
            {"test": "MRI", "result": "Artifact observed", "remarks": "Limited by metal interference"},
            {"test": "Orthopedic Note", "result": "Implant in good position", "remarks": "No loosening"}
        ]

        elif "periostealreaction" in fracture:
           test_results = [
            {"test": f"X-ray {hand.capitalize()} Long Bones", "result": f"{hand_prefix} Laminated periosteal reaction", "remarks": "Possible infection or tumor"},
            {"test": "MRI", "result": "No marrow involvement", "remarks": "Localized reaction"},
            {"test": "ESR/CRP", "result": "Raised inflammation markers", "remarks": "Suggests infection"}
        ]

        elif "pronatorsign" in fracture:
           test_results = [
            {"test": f"X-ray {hand.capitalize()} Elbow", "result": f"{hand_prefix} Anterior displacement of fat pad", "remarks": "Possible occult fracture"},
            {"test": "MRI", "result": "Soft tissue strain", "remarks": "Conservative treatment"},
            {"test": "Physical Exam", "result": "Pain with pronation", "remarks": "Splint advised"}
        ]

        elif "softtissue" in fracture:
            test_results = [
            {"test": f"Ultrasound {hand.capitalize()} Hand", "result": f"{hand_prefix} Edema in flexor tendon area", "remarks": "Compression and rest advised"},
            {"test": "MRI", "result": "No tendon rupture", "remarks": "Good prognosis"},
            {"test": "Blood Work", "result": "Normal WBC count", "remarks": "No active infection"}
        ]

        else:
           test_results = [
            {"test": "General X-ray", "result": "No clear diagnosis", "remarks": "Further evaluation recommended"}
        ]
           
        headers1 = {
            'Content-Type': 'application/json',
        }
        prompt2 = f"""
        Summarize the following clinical findings into a short medical summary suitable for a doctor's report:
        from the given data only summarize it to write only 2 lines to generate a small summary
        {prompt1}

"""

        data1 = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt2}
                    ]
                }
            ]
        }

        response2 = requests.post(url, headers=headers1, json=data1)
        response2.raise_for_status()

        result = response.json()
        summary = result['candidates'][0]['content']['parts'][0]['text']
        logging.info("My Summary is:")
        logging.info(summary)



        headers2 = {
            'Content-Type': 'application/json',
        }
        prompt3 = f"""tell me 3 points small recommendation in bullets points just According to their type of fracture only write 3 bullet points from given data
                    {latest_report.affected_hand}  and 
                    in this hand{latest_report.fracture_type} 
"""
        data2 = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt3}
                    ]
                }
            ]
        }

        response3 = requests.post(url, headers=headers2, json=data2)
        response3.raise_for_status()

        result = response.json()
        recommendation = result['candidates'][0]['content']['parts'][0]['text']

        logging.info("Now making the model insertion for the database of patient report")

        ###################### report model:
        report_content = f"""
        <h2>Comprehensive Medical Diagnostic Report</h2>
        <p><b>Patient Name:</b> {latest_report.name}</p>
        <p><b>Patient ID:</b> {latest_report.patient_code}</p>
        <p><b>Age:</b> {latest_report.age}</p>
        <p><b>Finding:</b> {latest_report.finding}</p>
        <p><b>Fracture type:</b> {latest_report.fracture_type}</p>
        <p><b>Hand Affected:</b> {latest_report.affected_hand}</p>

        <h3>Clinical History & Complaints</h3>
        {generated_report}

        <h3>Summary</h3>
        {summary}

        <h3>Recommendations</h3>
        {recommendation}
        """
        logging.info("----------------------------------------------------------------------------------------------")
        logging.info("working on the new work today for")

        buffer = BytesIO(report_content.encode("utf-8"))
        
        # Delete previous report if it exists (to avoid UNIQUE constraint error)
        try:
            previous_report = Patient_Report.objects.get(patient=latest_report.patient)
            previous_report.delete()
            logging.info("Previous report deleted")
        except Patient_Report.DoesNotExist:
            logging.info("No previous report found")
        
        # Create new report
        patient_report_file = Patient_Report(
            patient=latest_report.patient,
            Patient_name=latest_report.name,
            Patient_idx=latest_report.patient_code
        )
        
        logging.info("Till here working fine---------------------")
        patient_report_file.report_file.save(
            f"report_{latest_report.patient_code}.html", 
            ContentFile(buffer.getvalue())
        )
        logging.info("Insertion has been done")


        return render(request, 'Report.html', {
            'report': latest_report,
            'prompt1': markdown.markdown(generated_report),
            'test_results': test_results,
            'summary': markdown.markdown(summary),
            'recommendation' : markdown.markdown(recommendation)
        })
    except PatientXRayInfo.DoesNotExist:
        return render(request, 'Report.html', {
            'report': None,
            'prompt1': "No report found.",
            'test_results': [],
            'summary': "",
            'recommendation': ""
        })

    except Exception as e:
        return render(request, 'Report.html', {
            'report': None,
            'prompt1': f"Error generating report: {str(e)}",
            'test_results': [],
            'summary': "",
            'recommendation': ""
        })


def list_all_doctors(requests):
    
        Doctor_data = User.objects.all().values("id", "username", "doctor" , "password")
        admin_data = User.objects.all().values("id", "username", "admin" , "password")
        patient_data = PatientCreatedByDoctor.objects.all().values("doctor" ,
                                                                    "fname" ,
                                                                      "lname" ,
                                                                        "dob" ,
                                                                          "parents",
                                                                            "gender" ,
                                                                              "address")
        patient_work = [i for i in patient_data]
        admin_work = [i for i in admin_data]
        print("admin data is:" , admin_work)
        print("the patients data is:", patient_work)

        
        data = PatientXRayInfo.objects.all().values("name")

        send_data = [i for i in data]
        print("the given data is" , send_data)
        return JsonResponse(list(Doctor_data) ,  safe=False)


def Videos_Recommendation(request):
    try:
        fractures_types = ["boneanomaly" , 
                           "bonelesion" , 
                           "foreignbody" , 
                           "fracture" , 
                           "metal" , 
                           "periostealreaction" , 
                           "pronatorsign",
                           "softtissue" , 
                           "text"
                            ]
        

        return render(request , "Doctor/predict_vid.html")
    
    except Exception as e:
        raise {"issue" : str(e)}
    

def Displaying_videos(request , disease):
    try:
        folder_path = os.path.join(settings.STATICFILES_DIRS[0] , 'videos' , disease)
        logging.info("Yes found and the folder path is:")
        logging.info(folder_path)
        if not os.path.exists(folder_path):
            return JsonResponse({"error" : "not found"})
        
        videos = []
        for file in os.listdir(folder_path):
            if file.endswith((".mp4", ".webm", ".mov", ".avi")):
                videos.append({
                "title": file,
                "videoUrl": f"/static/videos/{disease}/{file}",
                "thumbnail": "/static/thumbnail.jpg",  
                "views": "0",
                "likes": "0"
            })
                
        logging.info("Videos data are is")
        logging.info(videos)

        return JsonResponse({"videos": videos})




    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=400)
    


def All_patient_reports(request):
    try:
        data =  Patient_Report.objects.all()
        print("the data getting is:" , data)
        return render(request, "report_list.html", {"reports": data})
    except Exception as e:
        return HttpResponse(str(e))

def logoutpage_doctor(request):
    logout(request)
    return redirect("loginSystem")



def Montoring_Exercise(request):
    try:
        return render(request , "Doctor/Video_Montoring.html")
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=404)
    



# === Load model and Mediapipe setup ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "exercise_autoencoder.h5")

# Lazy loading to avoid import-time errors
model = None
mp_pose = None
pose = None
frame_buffer = deque(maxlen=30)
THRESHOLD_GOOD, THRESHOLD_ALMOST = 0.02, 0.05

def get_model():
    global model, mp_pose, pose
    if model is None:
        try:
            model = load_model(MODEL_PATH, compile=False, safe_mode=False)
            mp_pose = mp.solutions.pose
            pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            return None, None, None
    return model, mp_pose, pose

def normalize_keypoints(landmarks):
    landmarks = np.array(landmarks).reshape(-1, 4)
    if landmarks.shape[0] >= 24:
        hip_center = (landmarks[23][:3] + landmarks[24][:3]) / 2
        landmarks[:, :3] -= hip_center
    landmarks[:, :3] /= np.linalg.norm(landmarks[:, :3]) + 1e-8
    return landmarks.flatten()

def extract_keypoints(frame):
    model, mp_pose, pose = get_model()
    if pose is None:
        return None
    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)
    if results.pose_landmarks:
        landmarks = []
        for lm in results.pose_landmarks.landmark:
            landmarks.extend([lm.x, lm.y, lm.z, lm.visibility])
        return normalize_keypoints(landmarks)
    return None

def check_exercise_quality(sequence):
    model, mp_pose, pose = get_model()
    if model is None:
        return "Model not available", 0.0, 1.0
    
    seq_padded = pad_sequences([sequence], maxlen=100, dtype='float32', padding='post', truncating='post')
    pred = model.predict(seq_padded, verbose=0)
    error = np.mean((seq_padded - pred) ** 2)
    confidence = max(0.0, 1.0 - (error / THRESHOLD_ALMOST))
    if error < THRESHOLD_GOOD: feedback = "Good ✅"
    elif error < THRESHOLD_ALMOST: feedback = "Almost 👍"
    else: feedback = "Not Correct ❌"
    return feedback, confidence, error

def monitor_view(request):
    return render(request, 'Doctor/Video_Montoring.html')

def process_frame(request):
    import json
    if request.method == 'POST':
        data = json.loads(request.body)
        frame_data = data['frame'].split(',')[1]
        image = Image.open(BytesIO(base64.b64decode(frame_data)))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        keypoints = extract_keypoints(frame)
        if keypoints is not None:
            frame_buffer.append(keypoints)

        feedback, confidence, error = "Waiting...", 0, 0
        if len(frame_buffer) == 30:
            sequence = np.array(frame_buffer)
            feedback, confidence, error = check_exercise_quality(sequence)


        return JsonResponse({
            'feedback': feedback,
            'confidence': float(confidence),
            'error': float(error)
        })


# =====================================================
# CHATBOT API ENDPOINT
# =====================================================

from main.services.chatbot_service import get_chatbot_service

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
@require_http_methods(["GET"])
def voice_test(request):
    """
    Render the voice recognition test/debug page
    GET /voice-test/
    """
    return render(request, 'voice_test.html')


@csrf_exempt
@require_http_methods(["POST"])
def chatbot_query(request):
    """
    API endpoint for chatbot query processing
    
    Receives a user query, processes it through Gemini AI with RAG on routes.yml,
    and returns the matched route path
    
    Request:
        POST /api/chatbot/query/
        {
            "query": "user text query"
        }
    
    Response:
        {
            "success": true/false,
            "matched_route": {...route info...},
            "path": "/url/path/",
            "message": "Navigation message",
            "reason": "Why this route was matched"
        }
    """
    try:
        # Parse request JSON
        data = json.loads(request.body)
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return JsonResponse({
                'success': False,
                'message': 'Query cannot be empty',
                'matched_route': None,
                'path': None
            }, status=400)
        
        # Get user roles (if user is authenticated)
        user_roles = ['anonymous']
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                user_roles = ['admin']
            else:
                # Check if user is a doctor or patient (based on your models)
                user_roles = ['doctor', 'patient']  # You may need to adjust this based on your User model
        
        # Get chatbot service and process query
        chatbot_service = get_chatbot_service()
        result = chatbot_service.process_query(user_query, user_roles)
        
        # Return result
        status_code = 200 if result.get('success') else 206  # 206 = Partial Content (fallback used)
        return JsonResponse(result, status=status_code)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON in request body',
            'matched_route': None,
            'path': None
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error in chatbot_query endpoint: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while processing your request',
            'matched_route': None,
            'path': None,
            'error': str(e)
        }, status=500)


@csrf_protect
def chatbot_debug(request):
    """
    DEBUG endpoint to test chatbot route matching
    Returns detailed information about how Gemini processed the query
    
    Request:
        POST /api/chatbot/debug/
        {
            "query": "user text query"
        }
    
    Response:
        {
            "query": "original user query",
            "gemini_response": "raw Gemini response",
            "parsed_result": {...parsed result...},
            "final_result": {...final JSON response...}
        }
    """
    try:
        data = json.loads(request.body)
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return JsonResponse({
                'error': 'Query cannot be empty'
            }, status=400)
        
        # Get user roles
        user_roles = ['anonymous']
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                user_roles = ['admin']
            else:
                user_roles = ['doctor', 'patient']
        
        # Get chatbot service
        chatbot_service = get_chatbot_service()
        
        # Get routes context
        routes_context = chatbot_service.format_routes_for_context(user_roles)
        
        # Call Gemini API
        gemini_response = chatbot_service.call_gemini_api(user_query, routes_context)
        
        # Parse response
        parsed = chatbot_service.parse_gemini_response(gemini_response)
        
        # Get final result
        final_result = chatbot_service.process_query(user_query, user_roles)
        
        return JsonResponse({
            'query': user_query,
            'gemini_response': gemini_response,
            'parsed_result': {
                'response_type': parsed[0],
                'route_id': parsed[1],
                'path': parsed[2],
                'reason': parsed[3],
                'answer': parsed[4],
                'form_fields': parsed[5],
                'button_to_click': parsed[6]
            },
            'final_result': final_result
        }, status=200)
    
    except Exception as e:
        logger.error(f"Error in chatbot_debug endpoint: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


# =====================================================
# PASSWORD RESET FUNCTIONALITY
# =====================================================

import logging
logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def request_password_reset(request):
    """
    Handle password reset request
    Request: POST /api/password-reset/request/
    Body: {"email": "user@example.com"}
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email is required'
            }, status=400)
        
        # Check if user exists by email in User model
        try:
            user = User.objects.get(email=email)
            logger.info(f"Password reset requested for user: {user.username} ({email})")
        except User.DoesNotExist:
            # For security, don't reveal if email exists
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return JsonResponse({
                'success': True,
                'message': 'If an account exists with this email, you will receive a password reset link shortly.'
            }, status=200)
        
        # Generate reset token
        reset_token = str(uuid.uuid4())
        user.reset_token = reset_token
        user.reset_token_created = timezone.now()
        user.save()
        logger.info(f"Reset token generated for user: {user.username}")
        
        # Send reset email with token
        subject = "Password Reset Request - X-Ai Medical Center"
        message = f"""
Hello {user.username},

You have requested to reset your password. Use the token below to reset your password:

PASSWORD RESET TOKEN:
{reset_token}

Copy this token and enter it in the password reset form to set your new password.

This token will expire in 24 hours.

If you did not request this, please ignore this email.

Best regards,
X-Ai Medical Center Team
"""
        
        try:
            send_mail(
                subject, 
                message, 
                'tauqeerqureshi112@gmail.com', 
                [email],
                fail_silently=False
            )
            logger.info(f"Password reset email sent successfully to: {email}")
        except Exception as email_error:
            logger.error(f"Failed to send password reset email to {email}: {email_error}")
            # Still return success to not reveal email configuration issues
            # But log it for debugging
            pass
        
        return JsonResponse({
            'success': True,
            'message': 'Check your email for the password reset token. You will need to enter it in the next step.'
        }, status=200)
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in password reset request")
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON in request'
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in password reset request: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while processing your request'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_reset_token(request):
    """
    Verify if reset token is valid
    Request: POST /api/password-reset/verify/
    Body: {"token": "reset_token"}
    """
    try:
        data = json.loads(request.body)
        token = data.get('token', '').strip()
        
        if not token:
            return JsonResponse({
                'success': False,
                'message': 'Token is required'
            }, status=400)
        
        # Check if token exists and is not expired (24 hour validity)
        try:
            user = User.objects.get(reset_token=token)
            
            # Check if token is still valid (24 hours)
            if user.reset_token_created:
                time_diff = timezone.now() - user.reset_token_created
                if time_diff.total_seconds() > 86400:  # 24 hours in seconds
                    return JsonResponse({
                        'success': False,
                        'message': 'Reset token has expired. Please request a new one.'
                    }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': 'Token is valid',
                'username': user.username
            }, status=200)
        
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid reset token'
            }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def reset_password(request):
    """
    Reset password with valid token
    Request: POST /api/password-reset/confirm/
    Body: {"token": "reset_token", "new_password": "password", "confirm_password": "password"}
    """
    try:
        data = json.loads(request.body)
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        # Validate inputs
        if not token or not new_password or not confirm_password:
            return JsonResponse({
                'success': False,
                'message': 'All fields are required'
            }, status=400)
        
        if new_password != confirm_password:
            return JsonResponse({
                'success': False,
                'message': 'Passwords do not match'
            }, status=400)
        
        if len(new_password) < 6:
            return JsonResponse({
                'success': False,
                'message': 'Password must be at least 6 characters long'
            }, status=400)
        
        # Find user with reset token
        try:
            user = User.objects.get(reset_token=token)
            
            # Check token expiry again
            if user.reset_token_created:
                time_diff = timezone.now() - user.reset_token_created
                if time_diff.total_seconds() > 86400:
                    return JsonResponse({
                        'success': False,
                        'message': 'Reset token has expired'
                    }, status=400)
            
            # Update password
            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_created = None
            user.save()
            
            # Send confirmation email
            subject = "Password Reset Successful - X-Ai Medical Center"
            message = f"""
Hello {user.username},

Your password has been successfully reset. You can now log in with your new password.

If you did not perform this action, please contact support immediately.

Best regards,
X-Ai Medical Center Team
"""
            send_mail(subject, message, 'tauqeerqureshi112@gmail.com', [user.email])
            
            return JsonResponse({
                'success': True,
                'message': 'Password has been reset successfully. You can now log in.'
            }, status=200)
        
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid reset token'
            }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON in request'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)


@login_required(login_url='admin_login')
def change_admin_password(request):
    """Allow admin to change their password without email verification"""
    if request.method == 'POST':
        try:
            current_password = request.POST.get('current_password', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()
            
            user = request.user
            
            # Verify current password
            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('change_admin_password')
            
            # Check if new passwords match
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                return redirect('change_admin_password')
            
            # Check password length
            if len(new_password) < 6:
                messages.error(request, 'New password must be at least 6 characters long.')
                return redirect('change_admin_password')
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Update session to avoid logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Password changed successfully!')
            return redirect('index_admin')
            
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('change_admin_password')
    
    return render(request, 'change_admin_password.html')


# New Pages Views

def about_page(request):
    """View for About Us page - Lightweight and fast"""
    return render(request, 'about.html')


def services_page(request):
    """View for Services page - Lightweight and fast"""
    return render(request, 'services.html')


def doctors_page(request):
    """View for Doctors/Team page - Lightweight and fast"""
    return render(request, 'doctors.html')


def contact_page(request):
    """View for Contact page - Lightweight and fast"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if name and email and subject and message:
            try:
                # Send email to hospital
                send_mail(
                    f'Contact Form: {subject}',
                    f'From: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}',
                    email,
                    ['tauqeerqureshi112@gmail.com'],
                    fail_silently=False,
                )
                messages.success(request, 'Your message has been sent successfully! We will contact you soon.')
                return redirect('contact_page')
            except Exception as e:
                messages.error(request, f'Error sending message. Please try again.')
                return redirect('contact_page')
        else:
            messages.error(request, 'Please fill all required fields.')
            return redirect('contact_page')
    
    return render(request, 'contact.html')


def faq_page(request):
    """View for FAQ page - Lightweight and fast"""
    return render(request, 'faq.html')
