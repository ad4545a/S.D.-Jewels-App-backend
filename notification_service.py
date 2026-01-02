import json
import os
import logging
from firebase_admin import messaging

ADMIN_TOKENS_FILE = "admin_tokens.json"

def load_admin_tokens():
    """Load admin FCM tokens from file"""
    try:
        if os.path.exists(ADMIN_TOKENS_FILE):
            with open(ADMIN_TOKENS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('admin_tokens', [])
        return []
    except Exception as e:
        logging.error(f"Failed to load admin tokens: {e}")
        return []

def save_admin_token(token):
    """Save a new admin FCM token"""
    try:
        tokens = load_admin_tokens()
        
        # Avoid duplicates
        if token not in tokens:
            tokens.append(token)
            
            with open(ADMIN_TOKENS_FILE, 'w') as f:
                json.dump({'admin_tokens': tokens}, f, indent=2)
            
            logging.info(f"Admin token saved. Total tokens: {len(tokens)}")
            return True
        else:
            logging.info("Token already exists")
            return True
    except Exception as e:
        logging.error(f"Failed to save admin token: {e}")
        return False

def send_error_notification(error_message, error_type="Server Error"):
    """Send error notification to all admin devices"""
    try:
        tokens = load_admin_tokens()
        
        if not tokens:
            logging.warning("No admin tokens registered. Cannot send notification.")
            return False
        
        # Create notification messages for each token
        messages = []
        for token in tokens:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"⚠️ {error_type}",
                    body=error_message,
                ),
                data={
                    'type': 'server_error',
                    'timestamp': str(os.times()),
                    'error': error_message
                },
                token=token,
            )
            messages.append(message)
        
        # Send to all admin devices
        response = messaging.send_each(messages)
        
        # Count successes and failures
        success_count = sum(1 for r in response.responses if r.success)
        failure_count = len(response.responses) - success_count
        
        # Log results
        logging.info(f"Notification sent: {success_count} success, {failure_count} failed")
        
        # Remove invalid tokens
        if failure_count > 0:
            failed_tokens = []
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    failed_tokens.append(tokens[idx])
                    logging.warning(f"Failed to send to token: {tokens[idx][:20]}... Error: {resp.exception}")
            
            # Clean up invalid tokens
            remove_invalid_tokens(failed_tokens)
        
        return success_count > 0
        
    except Exception as e:
        logging.error(f"Failed to send error notification: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False

def remove_invalid_tokens(invalid_tokens):
    """Remove invalid FCM tokens from storage"""
    try:
        tokens = load_admin_tokens()
        updated_tokens = [t for t in tokens if t not in invalid_tokens]
        
        with open(ADMIN_TOKENS_FILE, 'w') as f:
            json.dump({'admin_tokens': updated_tokens}, f, indent=2)
        
        logging.info(f"Removed {len(invalid_tokens)} invalid tokens")
    except Exception as e:
        logging.error(f"Failed to remove invalid tokens: {e}")

def send_server_stopped_notification():
    """Send notification when server is stopping"""
    send_error_notification(
        "Python server has stopped. Please check the logs and restart if needed.",
        "Server Stopped"
    )

def send_server_started_notification():
    """Send notification when server starts"""
    try:
        tokens = load_admin_tokens()
        
        if not tokens:
            logging.info("No admin tokens to notify about server start")
            return
        
        messages = []
        for token in tokens:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="✅ Server Started",
                    body="Python server is now running and monitoring market data.",
                ),
                data={
                    'type': 'server_started',
                },
                token=token,
            )
            messages.append(message)
        
        response = messaging.send_each(messages)
        success_count = sum(1 for r in response.responses if r.success)
        logging.info(f"Server start notification sent: {success_count} success")
        
    except Exception as e:
        logging.error(f"Failed to send server start notification: {e}")
        import traceback
        logging.error(traceback.format_exc())
