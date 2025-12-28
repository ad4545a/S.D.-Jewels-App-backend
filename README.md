# S.D. JEWELS - Price Robot Backend

This backend service powers the **S.D. JEWELS** mobile app. It acts as a "Robot" that connects to the commercial market API (Angel One), fetches live commodity data, applies business logic (margins/premiums), and updates the Firebase Realtime Database in real-time.

## ⚙️ Architecture

1.  **Market Data Source**: Angel One SmartAPI (MCX Gold, Silver, USDINR).
2.  **Processing**: Python script (`main.py`) running a continuous loop.
3.  **Database**: Firebase Realtime Database (pushes updates to the mobile app instantly).

## 🚀 Features

*   **Smart Fetching**: formatting Ask/Bid prices from Market Depth for accuracy.
*   **Connection Management**: Auto-reconnects to API and Database on failure.
*   **Business Logic**:
    *   Calculates "Derived Rates" (e.g., Gold 999 = MCX + Margin).
    *   Tracks High/Low for the session.
    *   Handles Market Open/Closed status.
*   **Currency Support**: Fetches USD/INR Futures for currency trends.

## 🛠️ Setup & Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/ad4545a/S.D.-Jewels-App-backend.git
    cd S.D.-Jewels-App-backend
    ```

2.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Credentials**:
    *   Ensure `google-services.json` (Firebase Admin SDK) is present.
    *   Update API Keys in `main.py` (Angel One Client ID, Password, TOTP Key).

4.  **Run the Robot**:
    ```bash
    python main.py
    ```

## 📂 File Structure

*   `main.py`: Core logic loop.
*   `fetch_tokens.py`: Utility to find current instrument tokens (Expiry management).
*   `inspect_api.py`: Debugging tool for API responses.
