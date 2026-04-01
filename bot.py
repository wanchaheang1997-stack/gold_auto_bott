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

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown"}
    if topic_id: payload["message_thread_id"] = topic_id
    try: requests.post(url, data=payload, timeout=15)
    except: pass

def get_market_data():
    symbols = ["GC=F", "XAUUSD=X"]
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            df_h1 = ticker.history(period="3d", interval="1h")
            df_m5 = ticker.history(period="1d", interval="5m")
            if not df_h1.empty: return df_h1, df_m5
        except: continue
    return pd.DataFrame(), pd.DataFrame()

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    df_h1, df_m5 = get_market_data()
    
    if df_h1.empty: return

    # 1️⃣ E11 CONCEPT (Session Liquidity)
    sessions = {'Tokyo': ('08:00', '10:00'), 'London': ('14:00', '16:00'), 'NY': ('19:00', '22:00')}
    zones = {}
    for s_name, (start, end) in sessions.items():
        d = df_h1.between_time(start, end)
        zones[s_name] = {'H': d['High'].max() if not d.empty else 0, 'L': d['Low'].min() if not d.empty else 0}

    # 2️⃣ SN1P3R VOLUME DELTA (CVD Flow)
    df_m5['Delta'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
    cvd_3 = df_m5['Delta'].tail(3).sum() # Delta 3 candles ចុងក្រោយ
    cvd_stat = "BULLISH 🟢" if cvd_3 > 0 else "BEARISH 🔴"

    # 3️⃣ BTRADER CONCEPT (CHoCH & Change in Character)
    # រកមើលការបំបែក Structure បែបលឿនៗ (Internal Structure)
    last_c = df_m5['Close'].iloc[-1]
    prev_h = df_m5['High'].shift(1).iloc[-1]
    prev_l = df_m5['Low'].shift(1).iloc[-1]
    
    is_choch_up = last_c > prev_h and cvd_3 > 0
    is_choch_down = last_c < prev_l and cvd_3 < 0

    # --- 📊 ផ្ញើ REPORT (តាមម៉ោង) ---
    if now_kh.hour in [8, 10, 14, 16, 19, 21, 22] and now_kh.minute < 15:
        report = (
            f"🏛 **SOVEREIGN TRINITY REPORT**\n"
            f"📅 `{now_kh.strftime('%H:%M')}` | Price: `${last_c:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **SN1P3R:** `{cvd_stat}` (Delta: {cvd_3:,.0f})\n"
            f"⚡ **BTRADER:** `Monitoring CHoCH...`\n"
            f"🗺 **E11:** `Watching Session High/Low`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- 🚨 ALERT (TRIPLE CONFLUENCE) ---
    for s_name, z in zones.items():
        if z['H'] == 0: continue
        
        # BUY SIGNAL: Price Sweep Low (E11) + CHoCH Up (BTrader) + Positive Delta (Sn1P3r)
        if last_c < z['L'] and is_choch_up:
            alert = (f"🔥 **TRINITY BUY SIGNAL**\n"
                     f"📍 Zone: {s_name} L Sweep\n"
                     f"⚡ BTrader: CHoCH Up ✅\n"
                     f"📊 Sn1P3r: Delta Positive ✅\n"
                     f"💰 Price: `${last_c:.2f}`")
            send_telegram(alert, TOPIC_ALERTS)
            
        # SELL SIGNAL: Price Sweep High (E11) + CHoCH Down (BTrader) + Negative Delta (Sn1P3r)
        elif last_c > z['H'] and is_choch_down:
            alert = (f"🔥 **TRINITY SELL SIGNAL**\n"
                     f"📍 Zone: {s_name} H Sweep\n"
                     f"⚡ BTrader: CHoCH Down ✅\n"
                     f"📊 Sn1P3r: Delta Negative ✅\n"
                     f"💰 Price: `${last_c:.2f}`")
            send_telegram(alert, TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
        
