import requests

# URLs for the registration and login endpoints
registration_url = 'http://localhost:8000/accounts/register/'
login_url = 'http://localhost:8000/accounts/login/'

# User data for testing
user_data = {
    'email': 'tes2t@example.com',
    'first_name': 'Test',
    'last_name': 'User',
    'password': 'password123'
}

def test_user_registration():
    """
    Test user registration endpoint.
    """
    response = requests.post(registration_url, data=user_data)
    assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
    print("Registration test passed.")

def test_user_login():
    """
    Test user login endpoint.
    """
    login_data = {
        'email': user_data['email'],
        'password': user_data['password']
    }
    response = requests.post(login_url, data=login_data)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    print("Login test passed.")

if __name__ == "__main__":
    test_user_registration()
    test_user_login()
