from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
import json

from main.validators import (
    validate_username,
    validate_password,
    validate_email,
    validate_phone_number,
    validate_image_file,
)
from main.services import AuthenticationService

User = get_user_model()


class ValidatorsTestCase(TestCase):
    """Test cases for input validators"""
    
    def test_validate_username_valid(self):
        """Test valid usernames"""
        self.assertEqual(validate_username("john_doe"), "john_doe")
        self.assertEqual(validate_username("user123"), "user123")
        self.assertEqual(validate_username("_test"), "_test")
    
    def test_validate_username_invalid_short(self):
        """Test username too short"""
        with self.assertRaises(ValidationError):
            validate_username("ab")
    
    def test_validate_username_invalid_chars(self):
        """Test username with invalid characters"""
        with self.assertRaises(ValidationError):
            validate_username("user@name")
    
    def test_validate_password_valid(self):
        """Test valid passwords"""
        valid_password = "SecurePass123"
        self.assertEqual(validate_password(valid_password), valid_password)
    
    def test_validate_password_invalid_short(self):
        """Test password too short"""
        with self.assertRaises(ValidationError):
            validate_password("Short1!")
    
    def test_validate_password_invalid_no_uppercase(self):
        """Test password without uppercase"""
        with self.assertRaises(ValidationError):
            validate_password("lowercase123")
    
    def test_validate_password_invalid_no_digit(self):
        """Test password without digit"""
        with self.assertRaises(ValidationError):
            validate_password("NoDigits!")
    
    def test_validate_email_valid(self):
        """Test valid emails"""
        self.assertEqual(
            validate_email("test@example.com"),
            "test@example.com"
        )
    
    def test_validate_email_invalid(self):
        """Test invalid emails"""
        with self.assertRaises(ValidationError):
            validate_email("invalid-email")
    
    def test_validate_phone_number_valid(self):
        """Test valid phone numbers"""
        self.assertEqual(validate_phone_number("1234567890"), "1234567890")
        self.assertEqual(validate_phone_number("+11234567890"), "+11234567890")
    
    def test_validate_phone_number_invalid(self):
        """Test invalid phone numbers"""
        with self.assertRaises(ValidationError):
            validate_phone_number("123")  # Too short
        with self.assertRaises(ValidationError):
            validate_phone_number("abc1234567890")  # Contains letters


class AuthenticationServiceTestCase(TestCase):
    """Test cases for authentication service"""
    
    def setUp(self):
        """Create test user"""
        self.test_username = "testuser"
        self.test_password = "SecurePass123"
        self.test_email = "test@example.com"
        self.user = User.objects.create_user(
            username=self.test_username,
            email=self.test_email,
            password=self.test_password,
            user_type='doctor'
        )
    
    def test_authenticate_user_valid(self):
        """Test successful user authentication"""
        user = AuthenticationService.authenticate_user(
            self.test_username,
            self.test_password
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.username, self.test_username)
    
    def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password"""
        user = AuthenticationService.authenticate_user(
            self.test_username,
            "WrongPassword123"
        )
        self.assertIsNone(user)
    
    def test_authenticate_user_invalid_username(self):
        """Test authentication with invalid username"""
        user = AuthenticationService.authenticate_user(
            "nonexistent",
            self.test_password
        )
        self.assertIsNone(user)
    
    def test_authenticate_user_type_filter(self):
        """Test authentication with user type filtering"""
        user = AuthenticationService.authenticate_user(
            self.test_username,
            self.test_password,
            user_type='doctor'
        )
        self.assertIsNotNone(user)
        
        # Try with wrong user type
        user = AuthenticationService.authenticate_user(
            self.test_username,
            self.test_password,
            user_type='admin'
        )
        self.assertIsNone(user)
    
    def test_create_user_valid(self):
        """Test successful user creation"""
        new_user = AuthenticationService.create_user(
            "newuser",
            "newuser@example.com",
            "SecurePass456",
            user_type='doctor'
        )
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.username, "newuser")
        self.assertTrue(new_user.check_password("SecurePass456"))
    
    def test_create_user_duplicate_username(self):
        """Test user creation with duplicate username"""
        with self.assertRaises(ValidationError):
            AuthenticationService.create_user(
                self.test_username,  # Already exists
                "different@example.com",
                "SecurePass456"
            )
    
    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email"""
        with self.assertRaises(ValidationError):
            AuthenticationService.create_user(
                "differentuser",
                self.test_email,  # Already exists
                "SecurePass456"
            )
    
    def test_create_user_invalid_password(self):
        """Test user creation with invalid password"""
        with self.assertRaises(ValidationError):
            AuthenticationService.create_user(
                "anotheruser",
                "another@example.com",
                "weak"  # Too short and invalid
            )


class LoginViewTestCase(TestCase):
    """Test cases for login views"""
    
    def setUp(self):
        """Create test client and user"""
        self.client = Client()
        self.test_username = "testdoctor"
        self.test_password = "SecurePass123"
        self.test_email = "testdoctor@example.com"
        
        # Create doctor user
        self.doctor = User.objects.create_user(
            username=self.test_username,
            email=self.test_email,
            password=self.test_password,
            user_type='doctor'
        )
        
        # Create admin user
        self.admin = User.objects.create_user(
            username="testadmin",
            email="testadmin@example.com",
            password=self.test_password,
            user_type='admin'
        )
        
        # Create patient user
        self.patient = User.objects.create_user(
            username="testpatient",
            email="testpatient@example.com",
            password=self.test_password,
            user_type='patient'
        )
    
    def test_doctor_login_valid(self):
        """Test successful doctor login"""
        response = self.client.post(
            reverse('login_doctor'),
            {
                'username': self.test_username,
                'password': self.test_password,
            }
        )
        # Should redirect to diagnosis_page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('diagnosis_page'))
    
    def test_doctor_login_invalid_credentials(self):
        """Test doctor login with invalid credentials"""
        response = self.client.post(
            reverse('login_doctor'),
            {
                'username': self.test_username,
                'password': 'wrongpassword',
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials')
    
    def test_doctor_login_missing_fields(self):
        """Test doctor login with missing fields"""
        response = self.client.post(
            reverse('login_doctor'),
            {
                'username': self.test_username,
                # Missing password
            }
        )
        self.assertEqual(response.status_code, 200)
    
    def test_admin_login_valid(self):
        """Test successful admin login"""
        response = self.client.post(
            reverse('admin_login'),
            {
                'username': 'testadmin',
                'password': self.test_password,
            }
        )
        # Should redirect to index_admin
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index_admin'))
    
    def test_admin_login_as_doctor(self):
        """Test admin login attempt with doctor account"""
        response = self.client.post(
            reverse('admin_login'),
            {
                'username': self.test_username,  # Doctor account
                'password': self.test_password,
            }
        )
        # Should fail - not an admin
        self.assertEqual(response.status_code, 200)
    
    def test_patient_login_valid(self):
        """Test successful patient login"""
        response = self.client.post(
            reverse('patient_login'),
            {
                'username': 'testpatient',
                'password': self.test_password,
            }
        )
        # Should redirect to patient_dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('patient_dashboard'))
    
    def test_patient_login_as_doctor(self):
        """Test patient login attempt with doctor account"""
        response = self.client.post(
            reverse('patient_login'),
            {
                'username': self.test_username,  # Doctor account
                'password': self.test_password,
            }
        )
        # Should fail - not a patient
        self.assertEqual(response.status_code, 200)


class SignupViewTestCase(TestCase):
    """Test cases for signup view"""
    
    def setUp(self):
        """Create test client"""
        self.client = Client()
    
    def test_signup_valid(self):
        """Test successful signup"""
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'newdoctor',
                'email': 'newdoctor@example.com',
                'password': 'SecurePass123',
            }
        )
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
        # Check user was created
        user = User.objects.filter(username='newdoctor').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'newdoctor@example.com')
    
    def test_signup_duplicate_username(self):
        """Test signup with duplicate username"""
        # Create first user
        User.objects.create_user(
            username='duplicate',
            email='first@example.com',
            password='SecurePass123',
            user_type='doctor'
        )
        
        # Try to create another with same username
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'duplicate',
                'email': 'second@example.com',
                'password': 'SecurePass123',
            }
        )
        # Should show error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already')
    
    def test_signup_invalid_email(self):
        """Test signup with invalid email"""
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'testuser',
                'email': 'invalid-email',
                'password': 'SecurePass123',
            }
        )
        self.assertEqual(response.status_code, 200)
    
    def test_signup_weak_password(self):
        """Test signup with weak password"""
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'weak',  # Too weak
            }
        )
        self.assertEqual(response.status_code, 200)
