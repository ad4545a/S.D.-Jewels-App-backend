import time
import datetime
import pytz
import json
import logging
import sys
import atexit
import signal
import threading
from SmartApi import SmartConnect
from firebase_admin import credentials, db, initialize_app, messaging
from flask import Flask, request, jsonify
from flask_cors import CORS

import pyotp 
import os
from dotenv import load_dotenv
from notification_service import (
    save_admin_token, 
    send_error_notification, 
    send_server_stopped_notification,
    send_server_started_notification
)

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
START_HOUR = 9   # 9 AM
START_MINUTE = 0
END_HOUR = 23    # 11 PM
END_MINUTE = 55

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask App
app = Flask(__name__)
CORS(app)

def get_ist_time():
    return datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

# Throttling for error notifications to avoid spam
last_error_notif_time = 0
MIN_NOTIF_INTERVAL = 300 # 5 minutes

def notify_error_throttled(message, title="API Error"):
    global last_error_notif_time
    try:
        current_time = time.time()
        if current_time - last_error_notif_time > MIN_NOTIF_INTERVAL:
            send_error_notification(message, title)
            last_error_notif_time = current_time
            logging.info(f"Throttled Error Notification Sent: {message}")
        else:
            logging.warning(f"Error Notification Suppressed (Throttling): {message}")
    except Exception as e:
        logging.error(f"Failed to send throttled notification: {e}")

def is_market_open():
    now = get_ist_time()
    # logging.info(f"DEBUG: Checking Time. Now={now}, Weekday={now.weekday()}")
    
    # Check day of week (0=Mon, 6=Sun)
    if now.weekday() >= 5: # Sat=5, Sun=6.
        # logging.info("DEBUG: Market Closed (Weekend)")
        return False
    
    current_time = now.time()
    start_time = datetime.time(START_HOUR, START_MINUTE)
    end_time = datetime.time(END_HOUR, END_MINUTE)
    
    # logging.info(f"DEBUG: Time Check: {start_time} <= {current_time} <= {end_time}")
    return start_time <= current_time <= end_time

def setup_firebase():
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        initialize_app(cred, {
            'databaseURL': FIREBASE_DB_URL
        })
        logging.info("Firebase Connected.")
    except Exception as e:
        logging.error(f"Failed to connect to Firebase: {e}")
        send_error_notification(f"Failed to connect to Firebase: {str(e)}", "Firebase Error")
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
        send_error_notification(f"Angel One Login Failed: {str(e)}", "API Connection Error")
        return None

def get_live_prices(smartApiObj):
    # Fetching Best Ask, High, Low
    token_gold = "449534" # GOLD05FEB26FUT
    token_silver = "451666" # SILVER05MAR26FUT
    token_usdinr = "1" # USDINR Spot Rate
    
    gold_data_out = {"price": 0.0, "high": 0.0, "low": 0.0, "bid": 0.0}
    silver_data_out = {"price": 0.0, "high": 0.0, "low": 0.0, "bid": 0.0}
    usd_data_out = {"price": 0.0}

    try:
        # Batch Request for MCX (Gold + Silver)
        tokens_mcx = {"MCX": [token_gold, token_silver]}
        res_mcx = smartApiObj.getMarketData("FULL", tokens_mcx)
        
        if res_mcx.get('status') and res_mcx.get('data'):
            fetched_list = res_mcx['data']['fetched']
            
            # Process results (Order isn't guaranteed, map by symbol or token)
            # Since we only passed tokens, we can match by token or just iterate.
            # However, the response usually corresponds to the request list or contains the token.
            # Let's support flexible parsing.
            
            for item in fetched_list:
                tk = item.get('tradingSymbol', '') # Or token could be checked
                # Note: SmartAPI returns 'tradingSymbol' e.g. "GOLD05FEB26FUT". 
                # We can also check tokens if returned. Usually they return 'symbolToken'.
                
                sym_token = item.get('symbolToken', '')
                
                # Determine if this is Gold or Silver
                target_dict = None
                if sym_token == token_gold:
                    target_dict = gold_data_out
                elif sym_token == token_silver:
                    target_dict = silver_data_out
                
                if target_dict is not None:
                    # Ask Price (Sell Depth)
                    depth_sell = item.get('depth', {}).get('sell', [])
                    if depth_sell:
                        target_dict['price'] = float(depth_sell[0]['price'])
                    else:
                        target_dict['price'] = float(item.get('ltp', 0.0))

                    # Bid Price (Buy Depth)
                    depth_buy = item.get('depth', {}).get('buy', [])
                    if depth_buy:
                         target_dict['bid'] = float(depth_buy[0]['price'])
                    else:
                         # Fallback to LTP if no depth
                         target_dict['bid'] = float(item.get('ltp', 0.0))

                    target_dict['high'] = float(item.get('high', 0.0))
                    target_dict['low'] = float(item.get('low', 0.0))
        elif not res_mcx.get('status'):
            if res_mcx.get('errorCode') == 'AG8001' or res_mcx.get('message') == 'Invalid Token':
                 raise Exception("Invalid Token")

    except Exception as e:
        if "Invalid Token" in str(e):
             raise
        error_msg = f"Failed to fetch MCX Data: {e}"
        logging.warning(error_msg)
        notify_error_throttled(error_msg, "MCX API Error")

    # No sleep between MCX and CDS needed if we want speed, maybe tiny yield?
    # time.sleep(0.05) 

    try:
        # 3. USDINR (CDS)
        tokens_usd = {"CDS": [token_usdinr]}
        res_usd = smartApiObj.getMarketData("LTP", tokens_usd) 
        
        # Debug: Log the response to see what we're getting
        logging.info(f"USDINR API Response: status={res_usd.get('status')}, data={res_usd.get('data')}")
        
        if res_usd.get('status') and res_usd.get('data'):
            fetched = res_usd['data'].get('fetched', [])
            if fetched and len(fetched) > 0:
                ltp = fetched[0].get('ltp', 0.0)
                if ltp > 0:
                    usd_data_out['price'] = float(ltp)
                    logging.info(f"USDINR Updated: {ltp}")
                else:
                    logging.warning(f"USDINR LTP is 0.0, keeping last value")
            else:
                logging.warning("USDINR: No data in fetched array")
        elif not res_usd.get('status'):
             if res_usd.get('errorCode') == 'AG8001' or res_usd.get('message') == 'Invalid Token':
                 raise Exception("Invalid Token")
              
              # We can get change percentage if needed from FULL, but LTP is basic start.
             
    except Exception as e:
        if "Invalid Token" in str(e):
             raise
        error_msg = f"Failed to fetch USDINR: {e}"
        logging.warning(error_msg)
        notify_error_throttled(error_msg, "USDINR API Error")
        
    return gold_data_out, silver_data_out, usd_data_out

def send_notification(title, body):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic='market_status',
        )
        response = messaging.send(message)
        logging.info(f"Notification Sent: {title} - {response}")
    except Exception as e:
        logging.error(f"Failed to send notification: {e}")

# ===== FLASK API ENDPOINTS =====

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'timestamp': str(datetime.datetime.now()),
        'server': 'Market Data Server'
    })

@app.route('/register-admin-token', methods=['POST'])
def register_admin_token():
    """Register admin FCM token for notifications"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        success = save_admin_token(token)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Admin token registered successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save token'
            }), 500
            
    except Exception as e:
        logging.error(f"Error registering admin token: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/send-test-notification', methods=['POST'])
def send_test_notification():
    """Send a test notification to all admin devices"""
    try:
        data = request.get_json() or {}
        message = data.get('message', 'This is a test notification from the server')
        
        success = send_error_notification(message, "Test Notification")
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Test notification sent'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send notification'
            }), 500
            
    except Exception as e:
        logging.error(f"Error sending test notification: {e}")
        return jsonify({'error': str(e)}), 500

# ===== MARKET MONITORING LOOP =====

def run_market_monitor():
    """Main market monitoring loop"""
    try:
        smartApi = login_angel_one()
        
        # Load last known values from Firebase instead of hardcoded defaults
        try:
            ref_live = db.reference('live_rates')
            stored_data = ref_live.get()
            if stored_data:
                last_gold = stored_data.get('gold', {})
                last_silver = stored_data.get('silver', {})
                last_usd = stored_data.get('usdinr', {})
                
                # Ensure we have price/high/low keys
                last_gold = {
                    "price": last_gold.get('mcx_price', 72000.0),
                    "high": last_gold.get('high', 72500.0),
                    "low": last_gold.get('low', 71800.0),
                    "bid": last_gold.get('bid', 71990.0) # Load bid or default
                }
                last_silver = {
                    "price": last_silver.get('mcx_price', 85000.0),
                    "high": last_silver.get('high', 86000.0),
                    "low": last_silver.get('low', 84500.0),
                    "bid": last_silver.get('bid', 84950.0) # Load bid or default
                }
                last_usd = {"price": last_usd.get('price', 83.50)}
                
                logging.info(f"Loaded last prices from DB: Gold={last_gold['price']}, Silver={last_silver['price']}, USD={last_usd['price']}")
            else:
                # Fallback to hardcoded if nothing in DB
                last_gold = {"price": 72000.0, "high": 72500.0, "low": 71800.0, "bid": 71950.0}
                last_silver = {"price": 85000.0, "high": 86000.0, "low": 84500.0, "bid": 84900.0}
                last_usd = {"price": 83.50}
                logging.info("No data in Firebase, using hardcoded defaults")
        except Exception as e:
            logging.warning(f"Failed to load last prices from Firebase: {e}. Using hardcoded defaults.")
            last_gold = {"price": 72000.0, "high": 72500.0, "low": 71800.0, "bid": 71950.0}
            last_silver = {"price": 85000.0, "high": 86000.0, "low": 84500.0, "bid": 84900.0}
            last_usd = {"price": 83.50}

        if not smartApi:
            logging.warning("Mock Mode - Fix Credentials")
            send_error_notification("Angel One API login failed. Server running in mock mode.", "API Warning")

        logging.info("Robot Started. Waiting for Market...")
        
        # State Tracking
        was_market_open = is_market_open() # Initial state
        logging.info(f"Initial Market State: {'Open' if was_market_open else 'Closed'}")

        while True:
            try:
                market_open = is_market_open()
                
                # Check for State Transition
                if market_open and not was_market_open:
                    # Closed -> Open
                    send_notification("Market Opened", "Values are live now! Check the latest Gold & Silver rates.")
                    was_market_open = True
                elif not market_open and was_market_open:
                    # Open -> Closed
                    send_notification("Market Closed", "Market has closed for the day. See you tomorrow!")
                    was_market_open = False


                # 1. Get Settings (ALWAYS fetch to pick up premium changes)
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
                m_usd_premium = float(margins.get('usd_premium', 0.0))
                m_gold_spot_premium = float(margins.get('gold_spot_premium', 0.0))
                m_silver_spot_premium = float(margins.get('silver_spot_premium', 0.0))

                # 2. Get Live Data (ONLY if Market Open)
                if market_open and smartApi:
                    try:
                        g_data, s_data, u_data = get_live_prices(smartApi)
                        
                        # Update if valid
                        if g_data['price'] > 0: last_gold = g_data
                        if s_data['price'] > 0: last_silver = s_data
                        if u_data['price'] > 0: last_usd = u_data
                    except Exception as e:
                        if "Invalid Token" in str(e):
                            logging.info("Token Expired (Invalid Token). Attempting to re-login...")
                            new_api_session = login_angel_one()
                            if new_api_session:
                                smartApi = new_api_session
                                logging.info("Re-login Successful. Resuming data fetch.")
                            else:
                                logging.error("Re-login Failed.")
                        else:
                            logging.error(f"Error fetching live prices: {e}")
                            notify_error_throttled(f"Error fetching live prices: {e}", "Live Data Error")

                # 3. Calculate Derived Rates (ALWAYS, using last known data + new margins)
                # Gold
                gold_mcx = last_gold['price']
                gold_999 = gold_mcx + m_gold_999
                gold_9950 = gold_mcx + m_gold_9950
                
                # Silver
                silver_mcx = last_silver['price']
                silver_9999 = silver_mcx + m_silver_9999
                silver_bars = silver_mcx + m_silver_bars 

                # Spot Calculation
                raw_usd = last_usd['price'] if last_usd['price'] > 0 else 83.50
                usd_rate = raw_usd + m_usd_premium # Apply Premium -> Effective USD
                
                # Formulas:
                # Gold Spot ($) = (MCX Gold / 10) / (USD * Factor) * 31.1035
                # Silver Spot ($) = (MCX Silver / 1000) / (USD * Factor) * 31.1035
                
                factor = 1.0935
                troy_oz = 31.1035
                
                gold_spot = 0.0
                if gold_mcx > 0:
                        gold_spot = ((gold_mcx / 10) / (usd_rate * factor) * troy_oz) + m_gold_spot_premium
                
                silver_spot = 0.0
                if silver_mcx > 0:
                        silver_spot = ((silver_mcx / 1000) / (usd_rate * factor) * troy_oz) + m_silver_spot_premium

                # 4. Update Firebase (ALWAYS)
                ref_live = db.reference('live_rates')
                
                # Determine status string
                status_str = 'Live' if market_open else 'Market Closed'
                
                payload = {
                    'gold': {
                        'mcx_price': gold_mcx,
                        'bid': last_gold.get('bid', gold_mcx - 10), # Include BID
                        'rate_999': gold_999,
                        'rate_9950': gold_9950,
                        'spot_price': round(gold_spot, 2),
                        'high': last_gold['high'],
                        'low': last_gold['low']
                    },
                    'silver': {
                        'mcx_price': silver_mcx,
                        'bid': last_silver.get('bid', silver_mcx - 50), # Include BID
                        'rate_9999': silver_9999,
                        'rate_bars': silver_bars,
                        'spot_price': round(silver_spot, 2),
                        'high': last_silver['high'],
                        'low': last_silver['low']
                    },
                    'usdinr': {
                        'price': usd_rate
                    },
                    'last_updated': str(datetime.datetime.now()),
                    'status': status_str
                }
                ref_live.set(payload)
                
                # Log occasionally (every ~60s if closed, else verbose?)
                # For now keeping verbose logic simple or reducing spam if closed?
                # Let's log updates.
                if market_open:
                     logging.info(f"Updated: G999={gold_999} S9999={silver_9999}")
                     time.sleep(0.05) # Fast updates when open
                else:
                     logging.info(f"Updated (Closed): G999={gold_999} S9999={silver_9999}")
                     time.sleep(5) # Slower updates when closed to save resources, but fast enough for UI tuning

            except KeyboardInterrupt:
                logging.info("Market monitor interrupted by user")
                break
            except Exception as e:
                error_msg = f"Loop Error: {str(e)}"
                logging.error(error_msg)
                send_error_notification(error_msg, "Market Monitor Error")
                time.sleep(5)

    except Exception as e:
        error_msg = f"Fatal error in market monitor: {str(e)}"
        logging.error(error_msg)
        send_error_notification(error_msg, "Fatal Server Error")
        raise

# ===== CLEANUP HANDLERS =====

def cleanup_handler():
    """Called when server is shutting down"""
    logging.info("Server shutting down...")
    send_server_stopped_notification()

def signal_handler(signum, frame):
    """Handle termination signals"""
    logging.info(f"Received signal {signum}")
    cleanup_handler()
    sys.exit(0)

# Register cleanup handlers
atexit.register(cleanup_handler)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ===== MAIN =====

def main():
    try:
        setup_firebase()
        
        # Send server started notification
        send_server_started_notification()
        
        # Start market monitor in a separate thread
        monitor_thread = threading.Thread(target=run_market_monitor, daemon=True)
        monitor_thread.start()
        
        # Run Flask server (blocking)
        logging.info("Starting Flask API server on port 5000...")
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        error_msg = f"Fatal error: {str(e)}"
        logging.error(error_msg)
        send_error_notification(error_msg, "Server Crash")
        raise

if __name__ == "__main__":
    main()
