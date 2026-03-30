import yfinance as yf
import pandas as pd
import numpy as np
import os
import requests
import pytz
import time
from datetime import datetime

# ========================================
# ⚙️ CONFIGURATION (ដាក់ Secret របស់បងនៅទីនេះ)
# ========================================
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = 8   # Daily Reports
TOPIC_ALERTS = 18    # High Prob Alerts
TIMEZONE = "Asia/Phnom_Penh"

# ========================================
# 📊 DATA FETCHING & SMC LOGIC
# ========================================
def get_data(symbol="GC=F"):
    ticker = yf.Ticker(symbol)
    df_h1 = ticker.history(period="10d", interval="1h")
    df_m15 = ticker.history(period="5d", interval="15m")
    df_m5 = ticker.history(period="2d", interval="5m")
    return df_h1, df_m15, df_m5

def detect_smc_setup(df_h1, df_m15, df_m5):
    """
    Step 1: Liquidity Sweep / SFP (H1/M15)
    Step 2: Confirmation (FVG/CHoCH) on M5
    """
    price = df_m5['Close'].iloc[-1]
    prev_h1_high = df_h1['High'].iloc[-2]
    prev_h1_low = df_h1['Low'].iloc[-2]
    
    setup_type = None
    bias = None
    
    # 1. Detect Sweep/SFP
    if price > prev_h1_high:
        setup_type = "BSL Sweep / SFP 🔴"
        bias = "SELL"
    elif price < prev_h1_low:
        setup_type = "SSL Sweep / SFP 🟢"
        bias = "BUY"
    
    if not setup_type: return None

    # 2. M5 Confirmation (FVG & CHoCH)
    # FVG Detection
    last_3 = df_m5.tail(3)
    fvg = (last_3['Low'].iloc[-1] > last_3['High'].iloc[-3]) or (last_3['High'].iloc[-1] < last_3['Low'].iloc[-3])
    
    # CHoCH (Structure Shift)
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
# 🧠 INTELLIGENCE & ANALYSIS
# ========================================
def get_market_intelligence(df_h1):
    change = df_h1['Close'].diff()
    buy_v = df_h1['Volume'][change > 0].sum()
    sell_v = df_h1['Volume'][change < 0].sum()
    buy_p = (buy_v / (buy_v + sell_v) * 100) if (buy_v + sell_v) > 0 else 50
    
    vol_sma = df_h1['Volume'].rolling(20).mean().iloc[-1]
    curr_vol = df_h1['Volume'].iloc[-1]
    manipulation = "⚠️ HIGH" if curr_vol > vol_sma * 1.8 else "Low"
    
    return round(buy_p, 1), manipulation

# ========================================
# 🤖 TELEGRAM ACTIONS
# ========================================
def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=10)
    except Exception as e: print(f"Error: {e}")

# ========================================
# 🚀 MAIN RUNNER (SCHEDULER & LOOP)
# ========================================
last_alert_id = None

def run_system():
    global last_alert_id
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    # 1. Fetch Data
    df_h1, df_m15, df_m5 = get_data()
    if df_h1.empty: return

    # 2. Daily Report Logic (Topic 8)
    # ចេញនៅនាទីទី 0 ដល់ 10 នៃម៉ោង 8, 14, 19
    if now_kh.hour in [8, 14, 19] and now_kh.minute < 10:
        buy_p, manipulation = get_market_intelligence(df_h1)
        report = (
            f"📊 **REPORT វិភាគមាស (XAU/USD)**\n"
            f"⏰ `{now_kh.strftime('%H:%M')} (Cambodia)`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠 **MARKET INTELLIGENCE**\n"
            f"• Buy Pressure: `{buy_p}%`\n"
            f"• Smart Money: `{manipulation}`\n"
            f"• Trend: `{'Bullish 🐂' if buy_p > 50 else 'Bearish 🐻'}`\n\n"
            f"🏗️ **SMC CONTEXT**\n"
            f"• PDH/PDL: `${df_h1['High'].iloc[-24:].max():,.2f}` / `${df_h1['Low'].iloc[-24:].min():,.2f}`\n"
            f"• Current: `${df_m5['Close'].iloc[-1]:,.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        send_telegram(report, TOPIC_ANALYSIS)
        time.sleep(600) # កុំឱ្យវាផ្ញើដដែលៗក្នុងរយៈពេល ១០នាទីនេះ

    # 3. Real-time Alert Logic (Topic 18)
    setup = detect_smc_setup(df_h1, df_m15, df_m5)
    if setup:
        alert_id = f"{setup['type']}_{setup['entry']}"
        if alert_id != last_alert_id:
            alert_msg = (
                f"🚨 **XAUUSD SMART ALERT**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔹 **Type:** `{setup['type']}`\n"
                f"📍 **Key Level:** `${setup['level']:,.2f}`\n\n"
                f"✅ **Confirmation:** `{setup['conf']} Detected`\n"
                f"💰 **Entry:** `${setup['entry']:,.2f}`\n"
                f"🎯 **Bias:** `{setup['bias']}`\n\n"
                f"💬 *Short Note:* Price swept liquidity at key level and showed displacement. High probability setup.*"
                f"\n━━━━━━━━━━━━━━━━━━━━"
            )
            send_telegram(alert_msg, TOPIC_ALERTS)
            last_alert_id = alert_id

if __name__ == "__main__":
    print("🚀 Bot is starting with Asia/Phnom_Penh Timezone...")
    while True:
        try:
            run_system()
        except Exception as e:
            print(f"Error in loop: {e}")
        time.sleep(60) # ឆែករាល់ ១ នាទី
        
