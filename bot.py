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

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    # ១. ទាញទិន្នន័យ (ប្រើ GC=F សម្រាប់ Gold Futures ដែលមាន Volume ច្បាស់ជាង)
    try:
        ticker = yf.Ticker("GC=F")
        df_h1 = ticker.history(period="3d", interval="1h")
        df_m5 = ticker.history(period="1d", interval="5m")
        if df_h1.empty or df_m5.empty: return
    except: return

    # --- 🛠 រូបមន្ត INDICATORS (FREE & CUSTOM) ---

    # A. E11 CONCEPT: រក Session High/Low (Liquidity Zones)
    sessions = {'Tokyo': ('08:00', '10:00'), 'London': ('14:00', '16:00'), 'NY': ('19:00', '22:00')}
    zones = {}
    for s_name, (start, end) in sessions.items():
        d = df_h1.between_time(start, end)
        zones[s_name] = {
            'H': d['High'].max() if not d.empty else 0,
            'L': d['Low'].min() if not d.empty else 0
        }

    # B. SN1P3R CONCEPT: គណនា Volume Delta (Buying vs Selling Pressure)
    # រូបមន្ត៖ បើតម្លៃបិទ > បើក = Volume វិជ្ជមាន (កម្លាំងទិញ)
    df_m5['Delta'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
    avg_vol = df_m5['Volume'].rolling(window=20).mean().iloc[-1]
    last_vol = df_m5['Volume'].iloc[-1]
    cvd_3 = df_m5['Delta'].tail(3).sum() # សរុបកម្លាំង ៣ Candle ចុងក្រោយ

    # C. BTRADER CONCEPT: រក CHoCH (Change of Character)
    # រូបមន្ត៖ តម្លៃបំបែក High ឬ Low នៃ Swing ចុងក្រោយ
    last_price = df_m5['Close'].iloc[-1]
    prev_high = df_m5['High'].iloc[-2]
    prev_low = df_m5['Low'].iloc[-2]
    
    is_choch_up = last_price > prev_high
    is_choch_down = last_price < prev_low

    # --- 📢 ការផ្ញើសារ ALERT (TRIPLE CONFLUENCE) ---
    for s_name, z in zones.items():
        if z['H'] == 0: continue
        
        # 🟢 BUY SIGNAL: Sweep Low (E11) + CHoCH Up (BTrader) + Big Volume (Sn1P3r)
        if last_price < z['L'] and is_choch_up and cvd_3 > 0:
            msg = (f"🔥 **TRINITY BUY SIGNAL**\n"
                   f"📍 Level: {s_name} Low Sweep (E11)\n"
                   f"⚡ Logic: CHoCH Up + Positive Delta\n"
                   f"📊 Volume: {'High ⚡' if last_vol > avg_vol else 'Normal'}\n"
                   f"💰 Price: `${last_price:.2f}`")
            send_telegram(msg, TOPIC_ALERTS)

        # 🔴 SELL SIGNAL: Sweep High (E11) + CHoCH Down (BTrader) + Big Volume (Sn1P3r)
        elif last_price > z['H'] and is_choch_down and cvd_3 < 0:
            msg = (f"🔥 **TRINITY SELL SIGNAL**\n"
                   f"📍 Level: {s_name} High Sweep (E11)\n"
                   f"⚡ Logic: CHoCH Down + Negative Delta\n"
                   f"📊 Volume: {'High ⚡' if last_vol > avg_vol else 'Normal'}\n"
                   f"💰 Price: `${last_price:.2f}`")
            send_telegram(msg, TOPIC_ALERTS)

    # --- 🏛 SESSION REPORT (ផ្ញើតាមម៉ោង) ---
    if now_kh.hour in [8, 10, 14, 16, 19, 21, 22, 23] and now_kh.minute < 15:
        report = (f"🏛 **SOVEREIGN TRINITY REPORT**\n"
                  f"📅 `{now_kh.strftime('%H:%M')}` | Price: `${last_price:.2f}`\n"
                  f"━━━━━━━━━━━━━━━━━━━━\n"
                  f"🌍 **SENTIMENT (Sn1P3r):**\n"
                  f"• Delta Flow: `{'BULLISH 🟢' if cvd_3 > 0 else 'BEARISH 🔴'}`\n"
                  f"• Vol Activity: `{last_vol:,.0f}`\n"
                  f"━━━━━━━━━━━━━━━━━━━━\n"
                  f"✅ *Watching BTrader CHoCH Confirmation*")
        send_telegram(report, TOPIC_ANALYSIS)

if __name__ == "__main__":
    run_system()
    
