import yfinance as yf
import pandas as pd
import numpy as np
import os
import requests
import pytz
from datetime import datetime

# ========================================
# ⚙️ CONFIGURATION (ដាក់ Secrets ក្នុង GitHub Settings)
# ========================================
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = 8   # សម្រាប់ Daily Reports
TOPIC_ALERTS = 18    # សម្រាប់ Real-time SMC Alerts
TIMEZONE = "Asia/Phnom_Penh"

# ========================================
# 📊 DATA FETCHING
# ========================================
def get_data(symbol="GC=F"):
    ticker = yf.Ticker(symbol)
    # ទាញទិន្នន័យសម្រាប់ Timeframe នីមួយៗ
    df_h1 = ticker.history(period="10d", interval="1h")
    df_m15 = ticker.history(period="5d", interval="15m")
    df_m5 = ticker.history(period="2d", interval="5m")
    return df_h1, df_m15, df_m5

# ========================================
# 🧠 SMC STRATEGY LOGIC (Sweep + Confirmation)
# ========================================
def detect_smc_setup(df_h1, df_m15, df_m5):
    price = df_m5['Close'].iloc[-1]
    prev_h1_high = df_h1['High'].iloc[-2]
    prev_h1_low = df_h1['Low'].iloc[-2]
    
    setup_type = None
    bias = None
    
    # 1. ឆែករក Liquidity Sweep (BSL/SSL)
    if price > prev_h1_high:
        setup_type = "BSL Sweep / SFP 🔴"
        bias = "SELL"
    elif price < prev_h1_low:
        setup_type = "SSL Sweep / SFP 🟢"
        bias = "BUY"
    
    if not setup_type: return None

    # 2. M5 Confirmation (FVG ឬ CHoCH)
    last_3 = df_m5.tail(3)
    fvg = (last_3['Low'].iloc[-1] > last_3['High'].iloc[-3]) or (last_3['High'].iloc[-1] < last_3['Low'].iloc[-3])
    
    recent_high = df_m5['High'].iloc[-10:-1].max()
    recent_low = df_m5['Low'].iloc[-10:-1].min()
    choch = (price > recent_high) if bias == "BUY" else (price < recent_low)

    if fvg or choch:
        return {
            "type": setup_type,
            "bias": bias,
            "level": prev_h1_high if bias == "SELL" else prev_h1_low,
            "conf": "FVG" if fvg else "CHoCH",
            "entry": price
        }
    return None

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
        requests.post(url, data=payload, timeout=15)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ========================================
# 🚀 SYSTEM RUNNER (NO LOOP FOR GITHUB ACTIONS)
# ========================================
def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    h, m = now_kh.hour, now_kh.minute

    print(f"🔍 Checking Markets at {now_kh.strftime('%H:%M:%S')}...")

    # 1. ទាញទិន្នន័យ
    df_h1, df_m15, df_m5 = get_data()
    if df_h1.empty: 
        print("❌ No data found!")
        return

    # 2. ផ្ញើ REPORT តាមម៉ោង SESSION (0-15 នាទីដំបូង)
    # 8=Asia, 14=London, 19=New York
    if h in [8, 14, 19] and m <= 15:
        buy_v = df_h1['Volume'][df_h1['Close'].diff() > 0].sum()
        sell_v = df_h1['Volume'][df_h1['Close'].diff() < 0].sum()
        buy_p = round((buy_v / (buy_v + sell_v) * 100), 1) if (buy_v + sell_v) > 0 else 50
        
        report = (
            f"📊 **XAU/USD SESSION REPORT**\n"
            f"⏰ `{now_kh.strftime('%H:%M')} (Cambodia)`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 **SENTIMENT**\n"
            f"• Trend: `{'Bullish 🐂' if buy_p > 50 else 'Bearish 🐻'}`\n"
            f"• Buy Pressure: `{buy_p}%`\n\n"
            f"🏗️ **STRUCTURE**\n"
            f"• Current: `${df_m5['Close'].iloc[-1]:,.2f}`\n"
            f"• PDH/PDL: `${df_h1['High'].iloc[-24:].max():,.2f}` / `${df_h1['Low'].iloc[-24:].min():,.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        send_telegram(report, TOPIC_ANALYSIS)
        print("✅ Analysis Report Sent.")

    # 3. ឆែករក ALERT (ផ្ញើភ្លាមៗពេលមាន Setup)
    setup = detect_smc_setup(df_h1, df_m15, df_m5)
    if setup:
        alert_msg = (
            f"🚨 **XAUUSD SMART ALERT**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔹 **Type:** `{setup['type']}`\n"
            f"📍 **Key Level:** `${setup['level']:,.2f}`\n"
            f"✅ **Confirmation:** `{setup['conf']}`\n\n"
            f"💰 **Entry:** `${setup['entry']:,.2f}`\n"
            f"🎯 **Bias:** `{setup['bias']}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        send_telegram(alert_msg, TOPIC_ALERTS)
        print("🚀 SMC Alert Sent.")

if __name__ == "__main__":
    # រត់តែម្តងគត់ រួច Exit ដើម្បីឱ្យ GitHub Actions Success
    run_system()
            
