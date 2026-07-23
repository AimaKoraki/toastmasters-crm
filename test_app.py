from fastapi.testclient import TestClient
from app.main import app
import traceback

try:
    client = TestClient(app)
    
    print("Testing GET /login")
    response = client.get("/login")
    print("Status:", response.status_code)
    if response.status_code >= 500:
        print(response.text)
        
    print("\nTesting GET / (unauthenticated)")
    response = client.get("/")
    print("Status:", response.status_code)
    
    print("\nTesting POST /login")
    response = client.post("/login", data={"passkey": "default-passkey-change-me"})
    print("Status:", response.status_code)
    
    print("\nTesting GET / (authenticated)")
    response = client.get("/")
    print("Status:", response.status_code)
    if response.status_code >= 500:
        print(response.text)
except Exception as e:
    traceback.print_exc()
