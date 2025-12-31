import os
from dotenv import load_dotenv
from SmartApi import SmartConnect
import pyotp

load_dotenv()

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_CODE = os.getenv("ANGEL_CLIENT_CODE")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_KEY = os.getenv("ANGEL_TOTP_KEY")

# Login
obj = SmartConnect(api_key=API_KEY)
totp_code = pyotp.TOTP(TOTP_KEY).now()
data = obj.generateSession(CLIENT_CODE, PASSWORD, totp_code)
print("✓ Logged in successfully")

# Search for USDINR contracts
print("\nSearching for USDINR contracts...")
response = obj.searchScrip("CDS", "USDINR")

if response['status']:
    contracts = response['data']
    print(f"\nFound {len(contracts)} USDINR contracts:")
    print("\nLooking for active FUT contracts:")
    for contract in contracts:
        # Only show FUT contracts
        if 'FUT' in contract.get('tradingsymbol', ''):
            token = contract.get('symboltoken', 'N/A')
            symbol = contract.get('tradingsymbol', 'N/A')
            name = contract.get('name', 'N/A')
            print(f"  Token: {token:8} | Symbol: {symbol:30} | Name: {name}")
else:
    print("Failed to search:", response)

# Test a few potential tokens
test_tokens = ["2122", "2123", "2124", "2125"]  
print("\nTesting tokens...")
for token in test_tokens:
    try:
        res = obj.getMarketData("LTP", {"CDS": [token]})
        if res['status'] and res['data']:
            fetched = res['data'].get('fetched', [])
            if fetched:
                print(f"  Token {token}: ✓ Active - LTP: {fetched[0].get('ltp', 'N/A')}")
            else:
                print(f"  Token {token}: ✗ No data (expired/inactive)")
        else:
            print(f"  Token {token}: ✗ Failed")
    except Exception as e:
        print(f"  Token {token}: ✗ Error - {e}")
