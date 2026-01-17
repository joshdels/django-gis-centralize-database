# Use for testing the DRF auth and its api/v1 features

import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

# ---- Login ----
data = {"username": "admin", "password": "admin1234567"}
r = requests.post(f"{BASE_URL}/login/", json=data)
token = r.json().get("token")
print("Token:", token)

# Headers
headers = {"Authorization": f"Token {token}"}

# ---- Get Projects ----
r = requests.get(f"{BASE_URL}/projects/", headers=headers)
print(r.json())

# ---- Logout ----
r = requests.post(f"{BASE_URL}/logout/", headers=headers)
print(r.json())
