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
TOPIC_STRUCTURE = 8   
TOPIC_ALERTS = 18    
TIMEZONE = "Asia/Phnom_Penh"

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown"}
    if topic_id: payload["message_thread_id"] = topic_id
    try: requests.post(url, data=payload, timeout=15)
    except: pass

def run_e11_v2():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    try:
        ticker = yf.Ticker("GC=F") # Gold Futures for better Volume
        df = ticker.history(period="3d", interval="5m")
        df_h1 = ticker.history(period="5d", interval="1h")
        if df.empty: return
    except: return

    # --- 1️⃣ E11 LIQUIDITY ZONES (High/Low of Sessions) ---
    sessions = {'Tokyo': ('08:00', '10:00'), 'London': ('14:00', '16:00'), 'NY': ('19:00', '22:00')}
    zones = {}
    for s, (start, end) in sessions.items():
        d = df_h1.between_time(start, end)
        zones[s] = {'H': d['High'].max(), 'L': d['Low'].min()}

    # --- 2️⃣ SN1P3R VOLUME DELTA (LuxAlgo Style) ---
    df['Delta'] = np.where(df['Close'] > df['Open'], df['Volume'], -df['Volume'])
    cvd_flow = df['Delta'].tail(5).sum()
    vol_sma = df['Volume'].rolling(20).mean().iloc[-1]
    curr_vol = df['Volume'].iloc[-1]

    # --- 3️⃣ BTRADER CHOCH & SFP LOGIC ($LSL / $LSH) ---
    last_c = df['Close'].iloc[-1]
    last_h = df['High'].iloc[-1]
    last_l = df['Low'].iloc[-1]
    prev_h = df['High'].iloc[-2]
    prev_l = df['Low'].iloc[-2]
    
    # CHoCH Confirmation (BTrader)
    choch_up = last_c > prev_h
    choch_down = last_c < prev_l

    # --- 📊 TOPIC 8: STRUCTURE REPORT (Every 15m) ---
    report = (
        f"🏛 **E11 CONCEPT 2.0 REPORT**\n"
        f"⏰ `{now_kh.strftime('%H:%M:%S')}` | Price: `${last_c:.2f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 **MARKET BIAS (Sn1P3r):**\n"
        f"• Flow: `{'BULLISH 🟢' if cvd_flow > 0 else 'BEARISH 🔴'}`\n"
        f"• Vol Strength: `{'HIGH ⚡' if curr_vol > vol_sma else 'LOW'}`\n\n"
        f"🗺 **LIQUIDITY ZONES (E11):**\n"
        f"• London High: `${zones['London']['H']:.1f}`\n"
        f"• NY Low: `${zones['NY']['L']:.1f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ *Monitoring $LSL/$LSH Sweep...*"
    )
    send_telegram(report, TOPIC_STRUCTURE)

    # --- 🚨 TOPIC 18: SNIPER ALERTS (Confirmation Only) ---
    for s, z in zones.items():
        # 🟢 $LSL (Liquidity Sweep Low) + CHoCH Up + Positive Delta
        if last_l < z['L'] and last_c > z['L'] and choch_up and cvd_flow > 0:
            alert = (f"🔥 **$LSL BUY SIGNAL (V2.0)**\n"
                     f"📍 Zone: {s} Low Sweep\n"
                     f"⚡ BTrader: CHoCH Up ✅\n"
                     f"📊 Sn1P3r: Delta Positive ✅\n"
                     f"💰 Entry Price: `${last_c:.2f}`")
            send_telegram(alert, TOPIC_ALERTS)

        # 🔴 $LSH (Liquidity Sweep High) + CHoCH Down + Negative Delta
        elif last_h > z['H'] and last_c < z['H'] and choch_down and cvd_flow < 0:
            alert = (f"🔥 **$LSH SELL SIGNAL (V2.0)**\n"
                     f"📍 Zone: {s} High Sweep\n"
                     f"⚡ BTrader: CHoCH Down ✅\n"
                     f"📊 Sn1P3r: Delta Negative ✅\n"
                     f"💰 Entry Price: `${last_c:.2f}`")
            send_telegram(alert, TOPIC_ALERTS)

if __name__ == "__main__":
    run_e11_v2()
    
