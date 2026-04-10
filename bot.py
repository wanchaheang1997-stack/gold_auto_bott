import yfinance as yf
import pandas as pd
import os, requests, pytz
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_REPORT = 8
TOPIC_ALERTS = 18

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown"}
    if topic_id: payload["message_thread_id"] = topic_id
    try:
        r = requests.post(url, data=payload, timeout=15)
        print(f"Telegram Response: {r.text}") # បង្ហាញលទ្ធផលក្នុង Logs របស់ GitHub
    except Exception as e:
        print(f"Telegram Error: {e}")

def run_v28_final():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    
    # FETCH DATA (XAUUSD)
    try:
        gold = yf.Ticker("GC=F")
        df_1h = gold.history(period="5d", interval="1h")
        if df_1h.empty:
            print("Error: Empty Data from Yahoo Finance")
            return
            
        curr_p = df_1h['Close'].iloc[-1]
        h1_ob_l, h1_ob_h = df_1h['Low'].iloc[-2], df_1h['High'].iloc[-2]

        # --- TEST ALERT (បាញ់រាល់ពេលឱ្យដឹងថា Bot រស់) ---
        test_msg = f"🔔 **E11 Sniper Online!**\n💰 Current Gold: `${curr_p:.2f}`\n📍 1H OB: `${h1_ob_l:.2f} - ${h1_ob_h:.2f}`"
        send_telegram(test_msg, TOPIC_REPORT) # សាកឱ្យវាបាញ់ចូល Report តែម្តងដើម្បីតេស្ត

        # --- REAL ALERT (Topic 18) ---
        if h1_ob_l <= curr_p <= h1_ob_h:
            alert_msg = f"🚨 **SNIPER ALERT: Price in 1H OB**\n💰 Price: `${curr_p:.2f}`"
            send_telegram(alert_msg, TOPIC_ALERTS)

    except Exception as e:
        print(f"Script Error: {e}")

if __name__ == "__main__":
    run_v28_final()
    
