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

def get_macro_data():
    try:
        tnx = yf.Ticker("^TNX").history(period="2d")['Close'].iloc[-1]
        gold = yf.Ticker("GC=F").history(period="2d")['Close'].iloc[-1]
        silver = yf.Ticker("SI=F").history(period="2d")['Close'].iloc[-1]
        return tnx, (gold / silver)
    except: return 0.0, 0.0

def get_cvd_bias(df_m5):
    df_m5 = df_m5.copy()
    # គណនា Delta Approximation
    df_m5['Delta'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
    cvd = df_m5['Delta'].tail(12).sum() # មើលកម្លាំងក្នុង ១ ម៉ោងចុងក្រោយ
    bias = "Aggressive Buying 🟢" if cvd > 0 else "Aggressive Selling 🔴"
    return cvd, bias

def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=15)
    except: pass

# ========================================
# 🚀 THE ULTIMATE RUNNER (V10.2)
# ========================================
def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    gold = yf.Ticker("GC=F")
    df_h1 = gold.history(period="5d", interval="1h")
    df_m5 = gold.history(period="2d", interval="5m")
    
    if df_h1.empty or df_m5.empty: return

    # គណនា Indicators ទាំងអស់
    yield_10y, gs_ratio = get_macro_data()
    cvd_val, cvd_bias = get_cvd_bias(df_m5)
    
    # ស្វែងរក Tokyo High/Low
    tokyo_data = df_h1.between_time('00:00', '07:00')
    tokyo_h = tokyo_data['High'].max()
    tokyo_l = tokyo_data['Low'].min()
    current_price = df_m5['Close'].iloc[-1]

    # --- [A] INSTITUTIONAL REPORT (Topic 8) ---
    # កំណត់ឱ្យផ្ញើរាល់ម៉ោងជួញដូរសំខាន់ៗ (រួមទាំងម៉ោង ២ រសៀលនេះ)
    if now_kh.hour in [8, 11, 14, 15, 19, 21]:
        report = (
            f"🏛 **SOVEREIGN MARKET REPORT**\n"
            f"📅 `{now_kh.strftime('%d %b | %H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 **MACRO DRIVERS:**\n"
            f"• US 10Y Yield: `{yield_10y:.2f}%`\n"
            f"• Gold/Silver Ratio: `{gs_ratio:.2f}`\n\n"
            f"🔥 **ORDER FLOW (CVD):**\n"
            f"• Market Bias: `{cvd_bias}`\n"
            f"• Flow Strength: `{abs(cvd_val):,.0f}`\n\n"
            f"🗺 **INTRADAY ZONES:**\n"
            f"• Tokyo High: `${tokyo_h:,.1f}`\n"
            f"• Tokyo Low: `${tokyo_l:,.1f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Analysis Ready - Check Alerts!*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- [B] SOVEREIGN ALERTS (Topic 18) ---
    last_m5 = df_m5.iloc[-1]
    
    # Logic: Sweep Tokyo High (Sell Setup)
    if last_m5['High'] > tokyo_h and last_m5['Close'] < tokyo_h:
        alert = (
            f"🚨 **SFP ALERT: TOKYO HIGH SWEEP**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Price: `${current_price:,.2f}`\n"
            f"📊 CVD Flow: `{cvd_bias}`\n"
            f"🏛 Zone: `Tokyo High Sweep` (SELL)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Wait for M1 MSS/CHoCH!*"
        )
        send_telegram(alert, TOPIC_ALERTS)
        
    # Logic: Sweep Tokyo Low (Buy Setup)
    elif last_m5['Low'] < tokyo_l and last_m5['Close'] > tokyo_l:
        alert = (
            f"🚨 **SFP ALERT: TOKYO LOW SWEEP**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Price: `${current_price:,.2f}`\n"
            f"📊 CVD Flow: `{cvd_bias}`\n"
            f"🏛 Zone: `Tokyo Low Sweep` (BUY)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Wait for M1 MSS/CHoCH!*"
        )
        send_telegram(alert, TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
                       
