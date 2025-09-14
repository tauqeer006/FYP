from django.shortcuts import render , redirect , HttpResponse, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate,login as auth_login , logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden,JsonResponse
from .models import PatientCreatedByDoctor,PatientXRayInfo
from datetime import date
from datetime import datetime
from django.core.files.storage import FileSystemStorage
import requests
import markdown


User = get_user_model()
def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        print("Username:", username)
        print("Password:", password)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            print("Authenticated:", user)
            if user.user_type == 'doctor': 
                auth_login(request, user)
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
       user = User.objects.create_user(username ,email ,  password)
       user.save()
       return redirect("loginSystem")
    return render(request , "signup.html")

def MainPage(request):
    return render(request , "index.html")


@login_required(login_url='admin_login')
def dashboard(request):
    user = request.user
    print(f"Dashboard accessed by: {user} with user_type: {getattr(user, 'user_type', None)}")
    if hasattr(user, 'user_type') and user.user_type == 'admin':
        return render(request, "index_admin.html")
    else:
        return HttpResponseForbidden("Access Denied: Admins only.")

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
            return redirect('index_admin1')
        else:
            messages.error(request, 'Access denied: Not an admin user or invalid credentials.')
            return render(request, 'admin_login.html')
    return render(request, 'admin_login.html')


def patient_login(request):
    return render(request , "patient_login.html")


def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password1')
        roles = request.POST.get('roles')
        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'add_user.html')
        if roles and roles.lower() == 'doctor':

            user = User.objects.create_user(username=username, password=password, user_type='doctor')
            user.user_type = 'doctor'  
            user.save()
            print("Doctor account has been created with username:", username , "password:" , password)
            messages.success(request, "Doctor user created successfully.")
            

        else:
            messages.error(request, "Role not recognized or not handled.")
    return render(request, 'index_admin.html')



def manage_user(request):

    visible_patients = PatientCreatedByDoctor.objects.filter(show_on_dashboard=True)

    pending_patients = PatientCreatedByDoctor.objects.filter(show_on_dashboard=False)

    return render(request, 'manage_user.html', {
        'visible_patients': visible_patients,
        'pending_patients': pending_patients,
    })

def toggle_dashboard_status(request, patient_id):
    patient = get_object_or_404(PatientCreatedByDoctor, id=patient_id)
    patient.show_on_dashboard = not patient.show_on_dashboard
    patient.save()
    return redirect('manageuser')
    

    
@login_required(login_url="loginSystem")
def diagnosis(request):
    return render(request , "base_doctor.html")


def add_patient(request):
    if request.method == 'POST':
        if not request.user.is_authenticated or request.user.user_type != 'doctor':
            return JsonResponse({"error": "Unauthorized access"}, status=403)
        fname = request.POST.get('fname')
        lname = request.POST.get("lname")
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        parents = request.POST.get('parents')
        contact_number = request.POST.get('contact_number')
        email = request.POST.get('email')
        address = request.POST.get('address')
        medical_history = request.POST.get('medical_history')
        PatientCreatedByDoctor.objects.create(

            doctor=request.user,
            fname = fname ,
            lname = lname,
            dob = dob,
            gender = gender,
            parents = parents,
            contact_number = contact_number  ,
            email = email ,
            address = address,
            medical_history = medical_history,

        )
        return render(request , "add_patient.html")

    return render(request , 'add_patient.html')




def get_all_patients_json(request):
    patients = PatientXRayInfo.objects.all()
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
    return render(request, 'new_diagnosis.html', {'patients': patients})


def predict_diagnosis(request):
    patients = PatientCreatedByDoctor.objects.all()

    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient_id')
            patient = PatientCreatedByDoctor.objects.get(id=patient_id)
            images = request.FILES.getlist('xray_images')

            if not images:
                return render(request, 'new_diagnosis.html', {
                    'patients': patients,
                    'error': 'No image uploaded'
                })

            image = images[0]  

            # ---------------------- Flask API 1: Fracture Detection ----------------------
            flask_url1 = 'http://localhost:5002/detect-fracture'
            response1 = requests.post(flask_url1, files={'image': image})
            fracture_data = response1.json()

            # ---------------------- Flask API 2: Left/Right Prediction ----------------------
            image.seek(0) 
            flask_url2 = 'http://localhost:5001/predict-lr'
            response2 = requests.post(flask_url2, files={'image': image})
            lr_data = response2.json()

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
        'name': prediction_result['patient_name'],
        'age': prediction_result['patient_age'],
        'patient_code': prediction_result['patient_id'],
        'xray_id': prediction_result['xray_id'],
        'finding': prediction_result['findings'],
        'fracture_type': prediction_result['fracture_types'][0],  
        'affected_hand': prediction_result['left_right'],
    }
)
            print(xray_info)
            

            return render(request, 'prediction.html', {
                'patients': patients,
                'prediction_result': prediction_result
            })

        except Exception as e:
            return render(request, 'new_diagnosis.html', {
                'patients': patients,
                'error': str(e)
            })

    return render(request, 'new_diagnosis.html', {
        'patients': patients
    })



def Report(request):
    try:
        latest_report = PatientXRayInfo.objects.latest('id')
        
        prompt1 = f"""
Generate a  medical diagnostic of fracture of small children report for the following patient.
Include the following sections:

1. 🔍 Clinical History & Presenting Complaints
Patient Details:
- Patient Name: {latest_report.name}
- Patient Code: {latest_report.patient_code}
- Age: {latest_report.age}
- Finding: {latest_report.finding}
- Affected Hand: {latest_report.affected_hand}
- Fracture Type: {latest_report.fracture_type}
- X-ray ID: {latest_report.xray_id}
tell me the medical dignosis according to type of fracture and on that hand not more than 3 4  dont write the detail of patietn just tell us about how 
this fracture ocurrs and in how many week it takes to get good 
"""

        api_key = "AIzaSyBXyZU6rOgwXtMSywB1ku-bAfq1JiIjsPM"
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

        """generating table:"""
        test_results = []

        if latest_report:
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
        {prompt1}
just listen the detail dont rewrite the complete data again just tell the short summary in 1 lines if no fracture found then write as no fracture found

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



        headers2 = {
            'Content-Type': 'application/json',
        }
        prompt3 = f"""
tell me 3 points small recommendation in bullets points just According to thei type of fracture {latest_report.affected_hand}  and in this hand{latest_report.fracture_type} 
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
        


    except PatientXRayInfo.DoesNotExist:
        latest_report = None
        generated_report = "No report found."

    except Exception as e:
        generated_report = f"Error generating report: {str(e)}"




    return render(request, 'Report.html', {
        'report': latest_report,
        'prompt1': markdown.markdown(generated_report),
        'test_results': test_results,
        'summary': markdown.markdown(summary),
        'recommendation' : markdown.markdown(recommendation)
    })

