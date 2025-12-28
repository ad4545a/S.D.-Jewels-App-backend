from SmartApi import SmartConnect
import pyotp
import logging
import time

# Metrics
API_KEY = "8APG7cjx"
CLIENT_CODE = "H58009686"
PASSWORD = "2000"
TOTP_KEY = "QSCHJBD3N2SDKHXVF7OEIYP5T4"

logging.basicConfig(level=logging.DEBUG)

def login():
    try:
        obj = SmartConnect(api_key=API_KEY)
        totp = pyotp.TOTP(TOTP_KEY).now()
        data = obj.generateSession(CLIENT_CODE, PASSWORD, totp)
        print("Login Success. Refresh Token:", data['data']['refreshToken'])
        return obj
    except Exception as e:
        print("Login Failed:", e)
        return None

def test_depth(obj):
    token_gold = "449534"
    print(f"\nTesting Individual getMarketData for Gold: {token_gold}")
    
    try:
        # According to some docs, exchangeTokens is a dict: {"MCX": ["token1", "token2"]}
        tokens_map = {
            "MCX": [token_gold]
        }
        print(f"Testing Map Payload: {tokens_map}")
        data = obj.getMarketData("FULL", tokens_map)
        print(f"Response (Map): {data}")
    except Exception as e:
        print(f"Error (Map): {e}")

    time.sleep(1)

    try:
        print("\nAttempting standard ltpData...")
        data = obj.ltpData("MCX", "GOLD", token_gold)
        print(f"Response (ltpData): {data}")
    except Exception as e:
        print(f"Error (ltpData): {e}")

if __name__ == "__main__":
    obj = login()
    if obj:
        test_depth(obj)
