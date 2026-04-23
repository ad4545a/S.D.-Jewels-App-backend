import firebase_admin
from firebase_admin import credentials, db
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("FIREBASE_KEY_PATH", "sd-jewels-firebase-adminsdk-fbsvc-8bfeb4c6ad.json")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")

print(f"Key Path: {SERVICE_ACCOUNT_FILE}")
print(f"DB URL:   {FIREBASE_DB_URL}")

try:
    # Initialize SDK if not already initialized
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DB_URL
        })
        print("Firebase Admin SDK Initialized.")
    else:
        print("Firebase Admin SDK already initialized.")

    # Reference to a test node
    ref = db.reference('server_test_write')

    # Data to write
    data = {
        'message': 'Hello from Python Server!',
        'timestamp': datetime.datetime.now().isoformat(),
        'status': 'success'
    }

    # Set data
    ref.set(data)
    print("Successfully wrote data to 'server_test_write' node.")
    
    # Read it back to confirm
    read_data = ref.get()
    print("Read back data:", read_data)

except Exception as e:
    print(f"Error: {e}")
