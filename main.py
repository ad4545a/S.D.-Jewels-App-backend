import time
import datetime
import pytz
import json
import logging
from SmartApi import SmartConnect
from firebase_admin import credentials, db, initialize_app

import pyotp 
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
# Angel One Credentials
API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_CODE = os.getenv("ANGEL_CLIENT_CODE")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_KEY = os.getenv("ANGEL_TOTP_KEY")

# Firebase
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
SERVICE_ACCOUNT_FILE = os.getenv("FIREBASE_KEY_PATH")

# Market Configuration
EXCHANGE = "MCX"
SYMBOL_GOLD = "GOLD" 
SYMBOL_SILVER = "SILVER"
# Note: For real trading, you need the instrument tokens. 
# We will implement a lookup or you must provide tokens.
# For now, we'll try to fetch tokens or use placeholders.

# Time Rules
START_HOUR = 14 # 2 PM
START_MINUTE = 0
END_HOUR = 23 # 11 PM
END_MINUTE = 55

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_ist_time():
    return datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

def is_market_open():
    return True # Force True for Testing/Closing Data
    
    # Original Logic commented out for now:
    # now = get_ist_time()
    # Check day of week (0=Mon, 6=Sun)
    # if now.weekday() >= 5: # Sat, Sun (Check if MCX is open Sat? Usually Mon-Fri)
    #     return False
    
    # current_time = now.time()
    # start_time = datetime.time(START_HOUR, START_MINUTE)
    # end_time = datetime.time(END_HOUR, END_MINUTE)
    
    # return start_time <= current_time <= end_time

def setup_firebase():
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        initialize_app(cred, {
            'databaseURL': FIREBASE_DB_URL
        })
        logging.info("Firebase Connected.")
    except Exception as e:
        logging.error(f"Failed to connect to Firebase: {e}")
        exit(1)

def login_angel_one():
    try:
        obj = SmartConnect(api_key=API_KEY)
        totp_code = pyotp.TOTP(TOTP_KEY).now()
        data = obj.generateSession(CLIENT_CODE, PASSWORD, totp_code)
        refreshToken = data['data']['refreshToken']
        feedToken = obj.getfeedToken()
        userProfile = obj.getProfile(refreshToken)
        logging.info(f"Angel One Connected. User: {userProfile['data']['name']}")
        return obj
    except Exception as e:
        logging.error(f"Angel One Login Failed: {e}")
        return None

def get_live_prices(smartApiObj):
    # Fetching Best Ask, High, Low
    token_gold = "449534" # GOLD05FEB26FUT
    token_silver = "451666" # SILVER05MAR26FUT
    token_usdinr = "2122" # USDINR25DECFUT

    gold_data_out = {"price": 0.0, "high": 0.0, "low": 0.0}
    silver_data_out = {"price": 0.0, "high": 0.0, "low": 0.0}
    usd_data_out = {"price": 0.0}

    try:
        # 1. Gold
        tokens_gold = {"MCX": [token_gold]}
        res_gold = smartApiObj.getMarketData("FULL", tokens_gold)
        if res_gold['status'] and res_gold['data']:
            fetched = res_gold['data']['fetched'][0]
            depth = fetched.get('depth', {}).get('sell', [])
            if depth:
                gold_data_out['price'] = float(depth[0]['price'])
            else:
                gold_data_out['price'] = float(fetched.get('ltp', 0.0))
            gold_data_out['high'] = float(fetched.get('high', 0.0))
            gold_data_out['low'] = float(fetched.get('low', 0.0))

    except Exception as e:
        logging.warning(f"Failed to fetch Gold: {e}")

    time.sleep(0.2) 

    try:
        # 2. Silver
        tokens_silver = {"MCX": [token_silver]}
        res_silver = smartApiObj.getMarketData("FULL", tokens_silver)
        if res_silver['status'] and res_silver['data']:
            fetched = res_silver['data']['fetched'][0]
            depth = fetched.get('depth', {}).get('sell', [])
            if depth:
                silver_data_out['price'] = float(depth[0]['price'])
            else:
                silver_data_out['price'] = float(fetched.get('ltp', 0.0))
            silver_data_out['high'] = float(fetched.get('high', 0.0))
            silver_data_out['low'] = float(fetched.get('low', 0.0))

    except Exception as e:
         logging.warning(f"Failed to fetch Silver: {e}")

    time.sleep(0.2)

    try:
        # 3. USDINR (CDS)
        tokens_usd = {"CDS": [token_usdinr]}
        res_usd = smartApiObj.getMarketData("LTP", tokens_usd) # LTP is enough for currency usually, or FULL
        if res_usd['status'] and res_usd['data']:
             fetched = res_usd['data']['fetched'][0]
             usd_data_out['price'] = float(fetched.get('ltp', 0.0))
             # We can get change percentage if needed from FULL, but LTP is basic start.
             
    except Exception as e:
        logging.warning(f"Failed to fetch USDINR: {e}")
        
    return gold_data_out, silver_data_out, usd_data_out

def main():
    setup_firebase()
    smartApi = login_angel_one()
    
    # Defaults
    last_gold = {"price": 72000.0, "high": 72500.0, "low": 71800.0}
    last_silver = {"price": 85000.0, "high": 86000.0, "low": 84500.0}
    last_usd = {"price": 83.50}

    if not smartApi:
        logging.warning("Mock Mode - Fix Credentials")

    logging.info("Robot Started. Waiting for Market...")

    while True:
        try:
            if is_market_open():
                # 1. Get Settings
                try:
                    ref_settings = db.reference('admin_settings')
                    settings = ref_settings.get() or {}
                except:
                    settings = {}
                
                margins = settings.get('margins', {})
                # Default margins if missing
                m_gold_999 = float(margins.get('gold_999', 0))
                m_gold_9950 = float(margins.get('gold_9950', 0))
                m_silver_9999 = float(margins.get('silver_9999', 0))
                m_silver_bars = float(margins.get('silver_bars', 0))

                # 2. Get Live Data
                if smartApi:
                    g_data, s_data, u_data = get_live_prices(smartApi)
                    
                    # Update if valid
                    if g_data['price'] > 0: last_gold = g_data
                    if s_data['price'] > 0: last_silver = s_data
                    if u_data['price'] > 0: last_usd = u_data
                
                # 3. Calculate Derived Rates
                # Gold
                gold_mcx = last_gold['price']
                gold_999 = gold_mcx + m_gold_999
                gold_9950 = gold_mcx + m_gold_9950
                
                # Silver
                silver_mcx = last_silver['price']
                silver_9999 = silver_mcx + m_silver_9999
                silver_bars = silver_mcx + m_silver_bars 

                # 4. Update Firebase
                ref_live = db.reference('live_rates')
                payload = {
                    'gold': {
                        'mcx_price': gold_mcx,
                        'rate_999': gold_999,
                        'rate_9950': gold_9950,
                        'high': last_gold['high'],
                        'low': last_gold['low']
                    },
                    'silver': {
                        'mcx_price': silver_mcx,
                        'rate_9999': silver_9999,
                        'rate_bars': silver_bars,
                        'high': last_silver['high'],
                        'low': last_silver['low']
                    },
                    'usdinr': {
                        'price': last_usd['price']
                    },
                    'last_updated': str(datetime.datetime.now()),
                    'status': 'Live'
                }
                ref_live.set(payload)
                
                logging.info(f"Updated: G999={gold_999} S9999={silver_9999} USD={last_usd['price']}")
            else:
                db.reference('live_rates/status').set('Market Closed')
                logging.info("Market Closed.")
                time.sleep(60)

            time.sleep(1)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Loop Error: {e}")
            time.sleep(5)


            break
        except Exception as e:
            logging.error(f"Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
