"""
Patient service module.
Handles patient management, creation, updates, and data retrieval.
"""

import logging
from django.core.exceptions import ValidationError
from django.db import transaction
from main.models import PatientCreatedByDoctor, PatientXRayInfo, PatientReport, User
from main.validators import validate_patient_data, validate_phone_number, validate_email

logger = logging.getLogger(__name__)


class PatientService:
    """Service for managing patient operations"""
    
    @staticmethod
    def create_patient(doctor_user, fname, lname, dob, gender, address, contact_number, email, medical_history=""):
        """
        Create a new patient record
        
        Args:
            doctor_user: User object of the doctor creating the patient
            fname (str): Patient first name
            lname (str): Patient last name
            dob (date): Date of birth
            gender (str): Gender (M/F/O)
            address (str): Address
            contact_number (str): Phone number
            email (str): Email address
            medical_history (str): Medical history
            
        Returns:
            PatientCreatedByDoctor object if successful
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate inputs
            patient_data = {
                'fname': fname,
                'lname': lname,
                'gender': gender,
                'age': 0,  # Will be calculated from DOB
                'contact_number': contact_number,
                'email': email,
            }
            validate_patient_data(patient_data)
            validate_phone_number(contact_number)
            validate_email(email)
            
            # Create patient using transaction
            with transaction.atomic():
                patient = PatientCreatedByDoctor.objects.create(
                    doctor=doctor_user,
                    fname=fname,
                    lname=lname,
                    dob=dob,
                    gender=gender,
                    address=address,
                    contact_number=contact_number,
                    email=email,
                    medical_history=medical_history,
                )
                logger.info(f"Patient created: {patient.id} by doctor {doctor_user.username}")
                return patient
        
        except ValidationError as e:
            logger.warning(f"Patient creation validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating patient: {e}", exc_info=True)
            raise ValidationError(f"Failed to create patient: {str(e)}")
    
    @staticmethod
    def get_patient(patient_id):
        """
        Retrieve a patient by ID
        
        Args:
            patient_id (int): Patient ID
            
        Returns:
            PatientCreatedByDoctor object or None
        """
        try:
            patient = PatientCreatedByDoctor.objects.get(id=patient_id)
            return patient
        except PatientCreatedByDoctor.DoesNotExist:
            logger.warning(f"Patient not found: {patient_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving patient: {e}")
            return None
    
    @staticmethod
    def update_patient(patient_id, **kwargs):
        """
        Update patient information
        
        Args:
            patient_id (int): Patient ID
            **kwargs: Fields to update
            
        Returns:
            Updated PatientCreatedByDoctor object or None
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            patient = PatientCreatedByDoctor.objects.get(id=patient_id)
            
            # Validate email if provided
            if 'email' in kwargs and kwargs['email']:
                validate_email(kwargs['email'])
            
            # Validate phone if provided
            if 'contact_number' in kwargs and kwargs['contact_number']:
                validate_phone_number(kwargs['contact_number'])
            
            # Update fields
            for field, value in kwargs.items():
                if hasattr(patient, field):
                    setattr(patient, field, value)
            
            patient.save()
            logger.info(f"Patient {patient_id} updated successfully")
            return patient
        
        except PatientCreatedByDoctor.DoesNotExist:
            logger.warning(f"Patient not found: {patient_id}")
            raise ValidationError(f"Patient {patient_id} not found")
        except ValidationError as e:
            logger.warning(f"Patient update validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating patient: {e}", exc_info=True)
            raise ValidationError(f"Failed to update patient: {str(e)}")
    
    @staticmethod
    def get_doctor_patients(doctor_user):
        """
        Get all patients for a specific doctor
        
        Args:
            doctor_user: User object of the doctor
            
        Returns:
            QuerySet of PatientCreatedByDoctor objects
        """
        try:
            patients = PatientCreatedByDoctor.objects.filter(
                doctor=doctor_user
            ).order_by('-created_at')
            logger.info(f"Retrieved {patients.count()} patients for doctor {doctor_user.username}")
            return patients
        except Exception as e:
            logger.error(f"Error retrieving doctor's patients: {e}")
            return PatientCreatedByDoctor.objects.none()
    
    @staticmethod
    def get_patient_xray_records(patient_id):
        """
        Get X-ray records for a patient
        
        Args:
            patient_id (int): Patient ID
            
        Returns:
            PatientXRayInfo object or None
        """
        try:
            xray_info = PatientXRayInfo.objects.get(patient_id=patient_id)
            return xray_info
        except PatientXRayInfo.DoesNotExist:
            logger.info(f"No X-ray records found for patient {patient_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving X-ray records: {e}")
            return None
    
    @staticmethod
    def save_xray_info(patient, doctor, name, age, patient_code, xray_id, finding, fracture_type, affected_hand):
        """
        Save or update X-ray information
        
        Args:
            patient: PatientCreatedByDoctor object
            doctor: User object of the doctor
            name (str): Patient name
            age (int): Patient age
            patient_code (str): Patient code
            xray_id (str): X-ray ID
            finding (str): Findings
            fracture_type (str): Type of fracture
            affected_hand (str): Affected hand (left/right)
            
        Returns:
            PatientXRayInfo object if successful
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            xray_info, created = PatientXRayInfo.objects.update_or_create(
                patient=patient,
                defaults={
                    'doctor': doctor,
                    'name': name,
                    'age': age,
                    'patient_code': patient_code,
                    'xray_id': xray_id,
                    'finding': finding,
                    'fracture_type': fracture_type,
                    'affected_hand': affected_hand,
                }
            )
            status = "created" if created else "updated"
            logger.info(f"X-ray info {status} for patient {patient.id}")
            return xray_info
        
        except Exception as e:
            logger.error(f"Error saving X-ray info: {e}", exc_info=True)
            raise ValidationError(f"Failed to save X-ray info: {str(e)}")
    
    @staticmethod
    def save_patient_report(patient, patient_name, patient_idx, report_file):
        """
        Save patient report (allows multiple reports per patient with ForeignKey)
        
        Args:
            patient: PatientCreatedByDoctor object
            patient_name (str): Patient name
            patient_idx (str): Patient index/code
            report_file: File object to save
            
        Returns:
            PatientReport object if successful
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Create new report (ForeignKey allows multiple reports per patient)
            report = PatientReport.objects.create(
                patient=patient,
                patient_name=patient_name,
                patient_idx=patient_idx,
                report_file=report_file
            )
            logger.info(f"Patient report saved for patient {patient.id}")
            return report
        
        except Exception as e:
            logger.error(f"Error saving patient report: {e}", exc_info=True)
            raise ValidationError(f"Failed to save patient report: {str(e)}")
    
    @staticmethod
    def get_patient_report(patient_id):
        """
        Get the latest report for a patient
        
        Args:
            patient_id (int): Patient ID
            
        Returns:
            PatientReport object or None
        """
        try:
            report = PatientReport.objects.filter(patient_id=patient_id).latest('created_at')
            return report
        except PatientReport.DoesNotExist:
            logger.info(f"No report found for patient {patient_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving patient report: {e}")
            return None
    
    @staticmethod
    def delete_patient(patient_id):
        """
        Delete a patient and related records
        
        Args:
            patient_id (int): Patient ID
            
        Returns:
            bool: True if deletion successful
        """
        try:
            with transaction.atomic():
                patient = PatientCreatedByDoctor.objects.get(id=patient_id)
                
                # Delete related records (cascade will handle these, but explicit for clarity)
                PatientXRayInfo.objects.filter(patient=patient).delete()
                PatientReport.objects.filter(patient=patient).delete()
                
                # Delete patient
                patient.delete()
                logger.info(f"Patient {patient_id} and related records deleted")
                return True
        
        except PatientCreatedByDoctor.DoesNotExist:
            logger.warning(f"Patient not found: {patient_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting patient: {e}", exc_info=True)
            return False
