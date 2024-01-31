import requests

# Endpoint API
login_url = 'http://localhost:8000/api/login/'

# Dane logowania
login_data = {
    'username': 'testuser2',  # Podmień na prawdziwą nazwę użytkownika
    'password': 'testpassword'  # Podmień na prawdziwe hasło
}

# Wysyłanie żądania POST do endpointu logowania
response = requests.post(login_url, data=login_data)

# Sprawdzanie odpowiedzi
if response.status_code == 200:
    print('Logowanie udane')
    print('Token:', response.json().get('token'))  # Wyświetlanie tokena
else:
    print('Błąd logowania:', response.status_code)
    #print(response.text)
