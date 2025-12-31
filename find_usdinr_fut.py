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
print("✓ Logged in successfully\n")

# Search for USDINR FUT contracts specifically
print("Searching for USDINR FUT contracts...")
response = obj.searchScrip("CDS", "USDINR")

if response['status']:
    contracts = response['data']
    print(f"Total USDINR contracts found: {len(contracts)}\n")
    
    # Filter for FUT contracts only and sort by token
    fut_contracts = []
    for contract in contracts:
        symbol = contract.get('tradingsymbol', '')
        if 'FUT' in symbol and 'USDINR' in symbol:
            fut_contracts.append(contract)
    
    print(f"USDINR FUT contracts: {len(fut_contracts)}\n")
    
    # Show first 20
    for contract in sorted(fut_contracts, key=lambda x: int(x.get('symboltoken', '0')))[:20]:
        token = contract.get('symboltoken', 'N/A')
        symbol = contract.get('tradingsymbol', 'N/A')
        name = contract.get('name', 'N/A')
        print(f"Token: {token:8} | Symbol: {symbol:30}")
        
        # Test this token
        try:
            res = obj.getMarketData("LTP", {"CDS": [token]})
            if res['status'] and res['data']:
                fetched = res['data'].get('fetched', [])
                if fetched and len(fetched) > 0:
                    ltp = fetched[0].get('ltp', 0)
                    if ltp > 0:
                        print(f"           ✓ ACTIVE - LTP: {ltp}")
                    else:
                        print(f"           ✗ LTP=0 (inactive)")
                else:
                    print(f"           ✗ No data")
        except:
            print(f"           ✗ Error")
else:
    print("Failed to search")
