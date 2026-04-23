import requests
import json
import time

# Configuration
# If testing locally, ensure main.py is running.
# If testing against VPS, use the VPS IP.
BASE_URL = "http://127.0.0.1:5000" 
# BASE_URL = "https://sd-jewels-backend.onrender.com"

def test_get_settings():
    print(f"Testing GET {BASE_URL}/admin/get-settings...")
    try:
        response = requests.get(f"{BASE_URL}/admin/get-settings")
        if response.status_code == 200:
            print("SUCCESS: Retrieved settings")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"FAILED: Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")

def test_update_margins():
    print(f"\nTesting POST {BASE_URL}/admin/update-margins...")
    payload = {
        "gold_999": 123.45,
        "silver_9999": 678.90,
        "ticker_text": "API Test Update " + str(time.time())
    }
    try:
        response = requests.post(f"{BASE_URL}/admin/update-margins", json=payload)
        if response.status_code == 200:
            print("SUCCESS: Updated settings")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"FAILED: Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    print("NOTE: Ensure main.py is running locally on port 5000 for this test.")
    test_get_settings()
    test_update_margins()
    # Verify update
    test_get_settings()
