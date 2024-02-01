from django.test import TestCase
from django.contrib.auth import get_user_model

class CustomUserModelTest(TestCase):
    def test_create_user(self):
        # This test verifies that a standard user can be created with the expected attributes.
        User = get_user_model()
        user = User.objects.create_user(
            email='normal@user.com', 
            password='foo', 
            first_name='first', 
            last_name='last'
        )
        # Asserting the attributes of the created user
        self.assertEqual(user.email, 'normal@user.com')
        self.assertEqual(user.first_name, 'first')
        self.assertEqual(user.last_name, 'last')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        # This test checks the creation of a superuser and ensures it has admin privileges.
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            'super@user.com', 
            'Super',
            'User',   
            'foo'     
        )
        # Asserting the attributes and privileges of the superuser
        self.assertEqual(admin_user.email, 'super@user.com')
        self.assertEqual(admin_user.first_name, 'Super')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)



from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

class UserRegistrationViewTest(APITestCase):
    def test_user_registration(self):
        # This test verifies the user registration process through the API endpoint.
        url = reverse('register')
        data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')
        # Checking if the API returns a 201 Created status, indicating successful registration.
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)



class UserLoginViewTest(APITestCase):
    def setUp(self):
        # Setup for login test: Creating a user to test the login process.
        self.user = get_user_model().objects.create_user(
            email='test@example.com', 
            password='password123', 
            first_name='Test', 
            last_name='User'
        )

    def test_user_login(self):
        # This test validates the user login functionality and token generation.
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')
        # Verifying successful login and token presence in the response.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


from .serializers import UserRegistrationSerializer, UserLoginSerializer

class UserRegistrationSerializerTest(TestCase):
    def test_valid_serializer(self):
        # Testing the serializer with valid data to ensure it validates correctly.
        valid_serializer_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'password123'
        }
        serializer = UserRegistrationSerializer(data=valid_serializer_data)
        # Asserting the serializer is valid when provided with correct data.
        self.assertTrue(serializer.is_valid())

    def test_invalid_serializer(self):
        # Testing the serializer with invalid data to ensure it rejects incomplete or incorrect data.
        invalid_serializer_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': ''
        }
        serializer = UserRegistrationSerializer(data=invalid_serializer_data)
        # Asserting the serializer is invalid when provided with incorrect data.
        self.assertFalse(serializer.is_valid())

# tests/test_serializers.py
from accounts.serializers import (
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetSerializer
)

# Test cases for PasswordChangeSerializer
class PasswordChangeSerializerTest(TestCase):
    # Test the serializer with valid data to ensure it validates correctly.
    # This checks the serializer's ability to handle correct data as expected.
    def test_serializer_with_valid_data(self):
        valid_data = {"old_password": "oldpassword", "new_password": "newsecurepassword"}
        serializer = PasswordChangeSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

    # Test the serializer with missing required fields to ensure it raises validation errors.
    # This validates the serializer's requirement for specific fields, enhancing security by ensuring password change requests include all necessary information.
    def test_serializer_with_missing_field(self):
        invalid_data = {"old_password": "oldpassword"}  # Missing new_password field
        serializer = PasswordChangeSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password", serializer.errors)

# Test cases for PasswordResetRequestSerializer
class PasswordResetRequestSerializerTest(TestCase):
    # Test the serializer with a valid email to ensure it validates correctly.
    # Validates the ability to initiate a password reset for valid user emails.
    def test_serializer_with_valid_email(self):
        valid_data = {"email": "user@example.com"}
        serializer = PasswordResetRequestSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

    # Test the serializer with an invalid email to ensure it raises validation errors.
    # Ensures that password reset requests reject improperly formatted email addresses.
    def test_serializer_with_invalid_email(self):
        invalid_data = {"email": "invalid-email"}  # Incorrect email format
        serializer = PasswordResetRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

# Test cases for PasswordResetSerializer
class PasswordResetSerializerTest(TestCase):
    # Test the serializer with all required fields provided and valid.
    # Checks the serializer's ability to handle the reset process with correct data.
    def test_serializer_with_valid_data(self):
        valid_data = {"token": "sometoken", "uid": "someuid", "new_password": "newsecurepassword"}
        serializer = PasswordResetSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

    # Test the serializer with missing fields to ensure it raises validation errors.
    # Validates that all necessary fields are present for password reset to proceed, ensuring the integrity of the reset process.
    def test_serializer_with_missing_field(self):
        invalid_data = {"token": "sometoken", "new_password": "newsecurepassword"}  # Missing uid field
        serializer = PasswordResetSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("uid", serializer.errors)



# tests/test_views.py
from rest_framework.test import APIClient
from .models import CustomUser  

class ChangePasswordViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a CustomUser instance using email and password
        self.user = CustomUser.objects.create_user(email='user@example.com', password='oldpassword', first_name='Test', last_name='User')
        
        # Log in to retrieve the token, using email and password
        response = self.client.post(reverse('login'), {'email': 'user@example.com', 'password': 'oldpassword'})
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg="Login failed")
        token = response.data['token']
        
        # Set the token in the Authorization header for subsequent requests
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        
        self.url = reverse('change-password')

    def test_change_password_success(self):
        data = {"old_password": "oldpassword", "new_password": "newsecurepassword"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_change_password_wrong_old_password(self):
        data = {"old_password": "wrongpassword", "new_password": "newsecurepassword"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

