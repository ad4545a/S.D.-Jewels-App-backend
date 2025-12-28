import urllib.request
import json
import datetime

url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

print("Downloading Scrip Master... (This might take a moment)")
try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        print(f"Downloaded {len(data)} scrips.")
        
        # Filter for MCX GOLD/SILVER and CDS USDINR
        scrips = [d for d in data if d['exch_seg'] == 'MCX' or d['exch_seg'] == 'CDS']
        
        def parse_date(date_str):
            # Format usually: 27MAY2025 or similar. Let's inspect or try parsing.
            # Angel One format examples: "28JAN2025"
            try:
                return datetime.datetime.strptime(date_str, "%d%b%Y").date()
            except:
                return datetime.date.max

        today = datetime.date.today()
        
        target_symbols = ["GOLD", "SILVER", "USDINR"]
        
        for target in target_symbols:
            # Find exact name matches (e.g. "GOLD" or "GOLDM" but usually "GOLD")
            # And expiry > today
            candidates = [
                d for d in scrips 
                if d['name'] == target and d['instrumenttype'] in ['FUTCOM', 'FUTCUR']
            ]
            
            # Sort by expiry
            candidates.sort(key=lambda x: parse_date(x['expiry']))
            
            # Get valid future ones
            valid_candidates = [c for c in candidates if parse_date(c['expiry']) >= today]
            
            if valid_candidates:
                nearest = valid_candidates[0]
                print(f"--- {target} ---")
                print(f"Symbol: {nearest['symbol']}")
                print(f"Token: {nearest['token']}")
                print(f"Expiry: {nearest['expiry']}")
            else:
                print(f"No valid future contracts found for {target}")

except Exception as e:
    print(f"Error: {e}")
