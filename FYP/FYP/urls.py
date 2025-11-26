"""
URL configuration for FYP project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.MainPage , name="MainPage"),
    path("login/", views.login_doctor , name="loginSystem"),
    path("signup/", views.signup , name="signupSystem"),
    path("index_admin/", views.dashboard , name="index_admin"),
    path("logout/", views.logoutpage , name="logout"),
    path("admin_login1/", views.admin_login1 , name="admin_login"),
    path("patient_login/", views.patient_login , name="patient_logins"),
    path("Patient_dashboard/" , views.patient_dashboard , name = "patient_dashboard"),
    path('add_user/', views.add_user, name='add_user'),
    path("/patient_Data" , views.user_profile , name = "user_profile"),
    path("/patient_complete_report" , views.user_report , name = "user_report"),
    path("/patient_complete_report" , views.detailed_history , name = "detailed_history"),
    path("/patient_logouts" , views.patient_logout , name = "patient_logout"),
   

    path('diagnosis/', views.diagnosis, name='diagnosis_page'),
    ### montoring Exercise:
    path("Montoring_Exericse/" , views.monitor_view , name = "Montoring_Exericse"),
    path('process_frame/', views.process_frame, name='process_frame'),
    ### works ends here.

    path('add_patient_record/' , views.add_patient , name="add_patient_record1"),
    path('manage_user/' , views.manage_user , name='manageuser'),
    path('toggle_dashboard/<int:patient_idx>/', views.toggle_dashboard_status, name='toggle_dashboard'),
    path('api/patients/', views.get_all_patients_json, name='get_all_patients_json'),
    path('patients/', views.get_all_patients, name='get_patient'),
    path('predict/', views.predict_diagnosis, name='predict_diagnosis'),
    path('Report/' , views.Report , name='Report_generation'),
    path("records/" , views.list_all_doctors , name = "all_data"),
    path("delete-doctor/<int:doctor_id>/" , views.remove_doctor , name = "remove_doctor"),
    path("graphs" , views.total_patient_graphs , name="graphs"),
    path("/video_Recommendation" , views.Videos_Recommendation , name = "Video-Recommendations"),
    path("Recommend_video/<str:disease>/" , views.Displaying_videos , name = "Display_Videos"),
    path("logout_doctor/", views.logoutpage_doctor , name="logout_doctor"),
    ## testing api:
    path("patient_data/" , views.patients_data , name="patient_work"),
    path("patient_reports/" , views.All_patient_reports , name= "patient_report"),
    
    ### new changes...
    # Chatbot API
    path('api/chatbot/query/', views.chatbot_query, name='chatbot_query'),
    path('api/chatbot/debug/', views.chatbot_debug, name='chatbot_debug'),
    path('voice-test/', views.voice_test, name='voice_test'),
    
    # Password Reset API
    path('api/password-reset/request/', views.request_password_reset, name='request_password_reset'),
    path('api/password-reset/verify/', views.verify_reset_token, name='verify_reset_token'),
    path('api/password-reset/confirm/', views.reset_password, name='reset_password'),
    
]
if settings.DEBUG:  # Only serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
