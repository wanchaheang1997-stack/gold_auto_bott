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
        requests.post(url, data=payload, timeout=15)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ========================================
# 📊 DATA FETCHING
# ========================================
def get_data():
    ticker = yf.Ticker("GC=F")
    # ទាញទិន្នន័យ H1 សម្រាប់ Structure និង M5 សម្រាប់ Entry
    df_h1 = ticker.history(period="10d", interval="1h")
    df_m5 = ticker.history(period="2d", interval="5m")
    return df_h1, df_m5

# ========================================
# 🚀 SYSTEM RUNNER (FULL VERSION)
# ========================================
def run_system():
    # 1. កំណត់ម៉ោងកម្ពុជាឱ្យបានច្បាស់
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    h, m = now_kh.hour, now_kh.minute

    print(f"🔍 System Running at: {now_kh.strftime('%Y-%m-%d %H:%M:%S')} (Cambodia)")

    # 2. ទាញទិន្នន័យ
    df_h1, df_m5 = get_data()
    if df_h1.empty or df_m5.empty: 
        print("❌ Error: No data fetched!")
        return

    current_price = df_m5['Close'].iloc[-1]
    prev_h1_high = df_h1['High'].iloc[-2]
    prev_h1_low = df_h1['Low'].iloc[-2]
    high_24h = df_h1['High'].tail(24).max()
    low_24h = df_h1['Low'].tail(24).min()

    # --- [A] FULL SESSION REPORT (Topic 8) ---
    # ឆែកម៉ោង Session: 8 (Asia), 11 (Test), 14 (London), 19 (NY)
    if h in [8, 11, 14, 19] and m <= 59:
        open_price = df_h1['Open'].iloc[-1]
        change = current_price - open_price
        change_pct = (change / open_price) * 100
        bias = "BULLISH 🐂" if change > 0 else "BEARISH 🐻"

        report = (
            f"📊 **XAU/USD INSTITUTIONAL REPORT**\n"
            f"⏰ `{now_kh.strftime('%H:%M:%S')} (Cambodia)`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 **MARKET SENTIMENT**\n"
            f"• Current Price: `${current_price:,.2f}`\n"
            f"• 24h Change: `{change:+.2f}$ ({change_pct:+.2f}%)`\n"
            f"• Bias: `{bias}`\n\n"
            f"🏗️ **STRUCTURE (H1)**\n"
            f"• Prev H1 High: `${prev_h1_high:,.2f}`\n"
            f"• Prev H1 Low: `${prev_h1_low:,.2f}`\n"
            f"• 24h Range: `${low_24h:,.2f}` - `${high_24h:,.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📢 *Monitoring Liquidity Sweeps...*"
        )
        send_telegram(report, TOPIC_ANALYSIS)
        print("✅ Full Report Sent.")

    # --- [B] SMC SMART ALERTS (Topic 18) ---
    # រក Swing High/Low ក្នុង M5 សម្រាប់ SL
    m5_high = df_m5['High'].tail(10).max()
    m5_low = df_m5['Low'].tail(10).min()

    setup = None
    # SELL: បើថ្លៃលើស H1 High (Liquidity Sweep)
    if current_price > prev_h1_high:
        entry = current_price
        sl = m5_high + 0.5
        tp = entry - ((sl - entry) * 2) # RR 1:2
        setup = {"type": "BSL Sweep / SFP 🔴", "bias": "SELL", "entry": entry, "tp": tp, "sl": sl}

    # BUY: បើថ្លៃទាបជាង H1 Low (Liquidity Sweep)
    elif current_price < prev_h1_low:
        entry = current_price
        sl = m5_low - 0.5
        tp = entry + ((entry - sl) * 2) # RR 1:2
        setup = {"type": "SSL Sweep / SFP 🟢", "bias": "BUY", "entry": entry, "tp": tp, "sl": sl}

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
            f"✅ **Conf:** `Liquidity Purged`"
        )
        send_telegram(alert_msg, TOPIC_ALERTS)
        print("🚀 SMC Alert Sent.")

if __name__ == "__main__":
    run_system()
        
