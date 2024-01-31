import requests

# Base URL of your Django server
BASE_URL = 'http://localhost:8000/accounts/'

# Endpoint URLs
change_password_url = BASE_URL + 'change-password/'
request_reset_url = BASE_URL + 'request-reset-password/'
reset_password_url = BASE_URL + 'reset-password/'

# User credentials for testing
user_data = {
    'email': 'adam.szczotka0@gmail.com',
    'old_password': 'password123',
    'new_password': 'newpassword123'
}
'''
# Headers for authenticated requests
headers = {'Authorization': 'Token your_token_here'}

# Test Password Change
response = requests.post(change_password_url, data={
    'old_password': user_data['old_password'],
    'new_password': user_data['new_password']
}, headers=headers)
print('Password Change Status:', response.status_code)
'''
# Test Password Reset Request
response = requests.post(request_reset_url, data={
    'email': user_data['email']
})
print('Password Reset Request Status:', response.status_code)


