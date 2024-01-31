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

