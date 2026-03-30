import yfinance as yf
import pandas as pd
import numpy as np
import os
import requests
import pytz
from datetime import datetime

# ========================================
# ⚙️ CONFIGURATION (GitHub Secrets)
# ========================================
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = 8   
TOPIC_ALERTS = 18    
TIMEZONE = "Asia/Phnom_Penh" # កំណត់យកម៉ោងកម្ពុជា UTC+7

# ========================================
# 📊 DATA FETCHING
# ========================================
def get_data(symbol="GC=F"):
    ticker = yf.Ticker(symbol)
    df_h1 = ticker.history(period="10d", interval="1h")
    df_m5 = ticker.history(period="2d", interval="5m")
    return df_h1, df_m5

# ========================================
# 🧠 SMC STRATEGY LOGIC (Sweep + Entry/TP/SL)
# ========================================
def detect_smc_setup(df_h1, df_m5):
    price = df_m5['Close'].iloc[-1]
    prev_h1_high = df_h1['High'].iloc[-2]
    prev_h1_low = df_h1['Low'].iloc[-2]
    
    # រក Swing High/Low ចុងក្រោយក្នុង M5 សម្រាប់ដាក់ SL
    recent_high = df_m5['High'].iloc[-10:-1].max()
    recent_low = df_m5['Low'].iloc[-10:-1].min()
    
    setup = None
    
    # 1. SELL SETUP (BSL Sweep + M5 Confirmation)
    if price > prev_h1_high:
        # បន្ថែមការឆែក M5 Choch/SFP បន្តិច
        if price < df_m5['High'].iloc[-2]: 
            entry = price
            sl = recent_high + 0.5 # SL លើ High ចុងក្រោយបន្តិច
            tp = entry - ((sl - entry) * 2) # RR 1:2
            setup = {
                "type": "BSL Sweep / SFP 🔴", "bias": "SELL",
                "entry": entry, "sl": sl, "tp": tp, "conf": "M5 Rejection"
            }

    # 2. BUY SETUP (SSL Sweep + M5 Confirmation)
    elif price < prev_h1_low:
        if price > df_m5['Low'].iloc[-2]:
            entry = price
            sl = recent_low - 0.5 # SL ក្រោម Low ចុងក្រោយបន្តិច
            tp = entry + ((entry - sl) * 2) # RR 1:2
            setup = {
                "type": "SSL Sweep / SFP 🟢", "bias": "BUY",
                "entry": entry, "sl": sl, "tp": tp, "conf": "M5 Rejection"
            }
            
    return setup

# ========================================
# 🤖 TELEGRAM ACTIONS
# ========================================
def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID, "text": text, 
        "parse_mode": "Markdown", "message_thread_id": topic_id
    }
    try:
        requests.post(url, data=payload, timeout=15)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ========================================
# 🚀 SYSTEM RUNNER (CAMBODIA TIME)
# ========================================
def run_system():
    # កំណត់ម៉ោងកម្ពុជា
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    h, m = now_kh.hour, now_kh.minute

    print(f"🔍 Checking Markets at {now_kh.strftime('%Y-%m-%d %H:%M:%S')} (Cambodia)")

    df_h1, df_m5 = get_data()
    if df_h1.empty: return

    # --- [A] ផ្ញើ SESSION REPORT (ម៉ោង 8, 14, 19 ខ្មែរ) ---
    if h in [8, 14, 19] and m <= 30:
        report = (
            f"📊 **XAU/USD SESSION REPORT**\n"
            f"⏰ `{now_kh.strftime('%H:%M')} (Cambodia)`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 **STATUS**\n"
            f"• Price: `${df_m5['Close'].iloc[-1]:,.2f}`\n"
            f"• Trend: `{'Bullish 🐂' if df_m5['Close'].iloc[-1] > df_h1['Open'].iloc[-1] else 'Bearish 🐻'}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        send_telegram(report, TOPIC_ANALYSIS)
        print("✅ Session Report Sent.")

    # --- [B] ឆែករក ALERT (Entry/TP/SL) ---
    setup = detect_smc_setup(df_h1, df_m5)
    if setup:
        alert_msg = (
            f"🚨 **XAUUSD SMART ALERT**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔹 **Type:** `{setup['type']}`\n"
            f"🎯 **Bias:** `{setup['bias']}`\n\n"
            f"💰 **ENTRY:** `${setup['entry']:,.2f}`\n"
            f"🟢 **TP:** `${setup['tp']:,.2f}` (RR 1:2)\n"
            f"🔴 **SL:** `${setup['sl']:,.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ **Conf:** `{setup['conf']}`"
        )
        send_telegram(alert_msg, TOPIC_ALERTS)
        print("🚀 SMC Alert Sent.")

if __name__ == "__main__":
    run_system()
    
