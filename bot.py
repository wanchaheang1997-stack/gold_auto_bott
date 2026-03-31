import yfinance as yf
import pandas as pd
import numpy as np
import os
import requests
import pytz
from datetime import datetime

# ========================================
# ⚙️ CONFIGURATION
# ========================================
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = 8   
TOPIC_ALERTS = 18    
TIMEZONE = "Asia/Phnom_Penh"

# ========================================
# 🤖 TELEGRAM ACTIONS
# ========================================
def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID, 
        "text": text, 
        "parse_mode": "Markdown", 
        "message_thread_id": topic_id
    }
    try:
        response = requests.post(url, data=payload, timeout=15)
        print(f"Telegram Status: {response.status_code}")
    except Exception as e:
        print(f"Telegram Error: {e}")

# ========================================
# 📊 DATA FETCHING
# ========================================
def get_data():
    ticker = yf.Ticker("GC=F")
    df_h1 = ticker.history(period="5d", interval="1h")
    df_m5 = ticker.history(period="1d", interval="5m")
    return df_h1, df_m5

# ========================================
# 🚀 SYSTEM RUNNER (FIXED CAMBODIA TIME)
# ========================================
def run_system():
    # 1. បង្ខំយកម៉ោងកម្ពុជាឱ្យបានច្បាស់ (UTC+7)
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    h = now_kh.hour
    m = now_kh.minute
    
    print(f"⏰ Current Time in Cambodia: {now_kh.strftime('%H:%M:%S')}")

    # 2. ទាញទិន្នន័យមាស
    df_h1, df_m5 = get_data()
    if df_h1.empty: 
        print("❌ Data Empty")
        return

    # --- [A] ផ្ញើ SESSION REPORT (Topic 8) ---
    # ខ្ញុំថែមលេខ 11 ចូល ដើម្បីឱ្យបងឃើញសារលោតក្នុង Telegram ឥឡូវនេះ (ម៉ោង ១១ ព្រឹក)
    # លក្ខខណ្ឌ m <= 59 គឺដើម្បីឱ្យបងចុច Test ពេលណាក៏វាផ្ញើដែរ ឱ្យតែស្ថិតក្នុងម៉ោងហ្នឹង
    if h in [8, 11, 14, 19] and m <= 59:
        print("📊 Sending Session Report...")
        current_price = df_m5['Close'].iloc[-1]
        
        report = (
            f"📊 **XAU/USD LIVE REPORT**\n"
            f"⏰ `{now_kh.strftime('%H:%M')} (Cambodia)`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Current Price:** `${current_price:,.2f}`\n"
            f"📈 **Market Status:** `Active`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- [B] ឆែករក SMC ALERTS (Topic 18) ---
    # (Logic SMC រក្សានៅដដែល ប៉ុន្តែបង្កើនល្បឿន Scan)
    prev_h1_high = df_h1['High'].iloc[-2]
    prev_h1_low = df_h1['Low'].iloc[-2]
    current_price = df_m5['Close'].iloc[-1]

    if current_price > prev_h1_high or current_price < prev_h1_low:
        bias = "SELL" if current_price > prev_h1_high else "BUY"
        # គណនា Entry, TP, SL 
        entry = current_price
        sl = (entry + 2) if bias == "SELL" else (entry - 2)
        tp = (entry - 4) if bias == "SELL" else (entry + 4)
        
        alert_msg = (
            f"🚨 **XAUUSD SMART ALERT**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **Bias:** `{bias}`\n"
            f"💰 **ENTRY:** `${entry:,.2f}`\n"
            f"🟢 **TP:** `${tp:,.2f}`\n"
            f"🔴 **SL:** `${sl:,.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        send_telegram(alert_msg, TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
    print("✅ Bot Task Finished.")
    
