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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.MainPage , name="MainPage"),
    path("login/", views.login , name="loginSystem"),
    path("signup/", views.signup , name="signupSystem"),
    path("index_admin/", views.dashboard , name="index_admin1"),
    path("logout/", views.logoutpage , name="logout"),
    path("admin_login1/", views.admin_login1 , name="admin_login"),
    path("patient_login/", views.patient_login , name="patient_logins"),
    path('add_user/', views.add_user, name='add_user'),
    path('diagnosis/', views.diagnosis, name='diagnosis_page'),
    path('add_patient_record/' , views.add_patient , name="add_patient_record1"),
    path('manage_user/' , views.manage_user , name='manageuser'),
    path('toggle_dashboard/<int:patient_id>/', views.toggle_dashboard_status, name='toggle_dashboard'),
    path('api/patients/', views.get_all_patients_json, name='get_all_patients_json'),
    path('patients/', views.get_all_patients, name='get_patient'),
    path('predict/', views.predict_diagnosis, name='predict_diagnosis'),
    path('Report/' , views.Report , name='Report_generation'),
    
]
