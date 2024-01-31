import requests

# Base URL of your Django server
BASE_URL = 'http://localhost:8000/accounts/'

# Endpoint URLs
change_password_url = BASE_URL + 'change-password/'
request_reset_url = BASE_URL + 'request-reset-password/'
reset_password_url = BASE_URL + 'reset-password/'



# Assuming we have the token and uid from the email,
# we simulate the password reset process.
# Note: Replace 'token_value' and 'uid_value' with actual values for a real test.
response = requests.post(reset_password_url, data={
    'token': 'token_value',
    'uid': 'uid_value',
    'new_password': 'newpassword123'
})
print('Password Reset Status:', response.status_code)