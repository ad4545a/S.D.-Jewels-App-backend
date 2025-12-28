from SmartApi import SmartConnect
import pyotp

# Credentials from main.py
API_KEY = "8APG7cjx" 
CLIENT_CODE = "H58009686" 
PASSWORD = "2000" 
TOTP_KEY = "QSCHJBD3N2SDKHXVF7OEIYP5T4"

try:
    obj = SmartConnect(api_key=API_KEY)
    totp_code = pyotp.TOTP(TOTP_KEY).now()
    data = obj.generateSession(CLIENT_CODE, PASSWORD, totp_code)
    
    print("Login Success. Searching...")
    
    # Search for GOLD
    print("--- GOLD ---")
    try:
        # Search for "GOLD"
        data = obj.searchScrip("MCX", "GOLD") 
        if data and data['status'] and data['data']:
            # Filter for futures, sort by expiry if possible or just print top 5
            # We want 'GLD' usually or 'GOLD'
            # Let's print the first few to pick manually or heuristics
            for i, scrip in enumerate(data['data'][:10]):
                print(f"{i}: {scrip['tradingsymbol']} (Token: {scrip['symboltoken']})")
        else:
            print("No data for GOLD")
    except Exception as e:
        print(f"Search Error GOLD: {e}")

    # Search for SILVER
    print("--- SILVER (Done) ---")
    # try:
    #     data = obj.searchScrip("MCX", "SILVER")
    #     if data and data['status'] and data['data']:
    #          for i, scrip in enumerate(data['data'][:10]):
    #             print(f"{i}: {scrip['tradingsymbol']} (Token: {scrip['symboltoken']})")
    #     else:
    #         print("No data for SILVER")
    # except Exception as e:
    #     print(f"Search Error SILVER: {e}")
except Exception as e:
    print(f"Error: {e}")
