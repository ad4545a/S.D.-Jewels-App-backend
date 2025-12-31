import os
from dotenv import load_dotenv
from SmartApi import SmartConnect
import pyotp
import json

load_dotenv()

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_CODE = os.getenv("ANGEL_CLIENT_CODE")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_KEY = os.getenv("ANGEL_TOTP_KEY")

# Login
obj = SmartConnect(api_key=API_KEY)
totp_code = pyotp.TOTP(TOTP_KEY).now()
data = obj.generateSession(CLIENT_CODE, PASSWORD, totp_code)
print("✓ Logged in\n")

# First, let's see what exchanges we can search
print("Testing different currency pairs on CDS:")
test_pairs = ["USDINR", "USD", "INR"]

for pair in test_pairs:
    print(f"\nSearching for '{pair}'...")
    try:
        response = obj.searchScrip("CDS", pair)
        if response['status'] and response['data']:
            contracts = response['data']
            print(f"  Found {len(contracts)} contracts")
            
            # Show first 5 with details
            for contract in contracts[:5]:
                symbol = contract.get('tradingsymbol', 'N/A')
                token = contract.get('symboltoken', 'N/A')
                print(f"    {token:10} | {symbol}")
        else:
            print(f"  No results")
    except Exception as e:
        print(f"  Error: {e}")

# Try testing the USDINR spot or direct lookup
print("\n\nTrying direct lookups with known token patterns...")
test_tokens = ["2122", "1", "2", "3", "4", "5", "10", "100", "1000"]

for token in test_tokens:
    try:
        res = obj.getMarketData("LTP", {"CDS": [token]})
        if res['status'] and res['data']:
            fetched = res['data'].get('fetched', [])
            if fetched:
                symbol = fetched[0].get('tradingSymbol', 'N/A')
                ltp = fetched[0].get('ltp', 0)
                print(f"Token {token}: {symbol:40} LTP={ltp}")
    except:
        pass
