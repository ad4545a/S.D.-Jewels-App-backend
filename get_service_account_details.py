import json
import os
from dotenv import load_dotenv

load_dotenv()

key_path = os.getenv("FIREBASE_KEY_PATH", "sd-jewels-firebase-adminsdk-fbsvc-8bfeb4c6ad.json")

print(f"Loading key from: {key_path}")

try:
    with open(key_path, 'r') as f:
        data = json.load(f)
        
    client_email = data.get('client_email')
    client_id = data.get('client_id')
    
    print("-" * 30)
    print(f"Service Account Email: {client_email}")
    print(f"Service Account ID:    {client_id}")
    print("-" * 30)
    print("\nNOTE: For Realtime Database Rules, the 'auth.uid' for a service account is typically the 'client_email'.")
    print(f"Recommended Rule UID: '{client_email}'")
    
except Exception as e:
    print(f"Error loading key: {e}")
