import requests

# Dane dostępowe do API
api_url = 'http://localhost:8000/api/'  # Zmień na odpowiedni adres URL Twojego API
register_url = f'{api_url}register/'  # Endpoint rejestracji
login_url = f'{api_url}login/'  # Endpoint logowania

# Przykładowe dane użytkownika do rejestracji
user_data = {
    'username': 'testuser2',
    'password': 'testpassword',
    'email': 'test@example.com',
}

# Rejestracja użytkownika
response = requests.post(register_url, data=user_data)
if response.status_code == 201:
    print('Rejestracja udana')
    print(response.json())  # Odpowiedź API
else:
    print('Błąd rejestracji')
    #print(response.text)  # Wiadomość o błędzie



