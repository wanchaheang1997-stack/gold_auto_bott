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
    try: 
        r = requests.post(url, data=payload, timeout=15)
        print(f"Telegram Log: {r.status_code}")
    except: print("❌ Connection Failed")

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    print(f"🚀 Bot Starting: {now_kh.strftime('%H:%M:%S')}")

    try:
        # ១. ទាញទិន្នន័យមាស (XAUUSD)
        ticker = yf.Ticker("XAUUSD=X")
        df_h1 = ticker.history(period="3d", interval="1h")
        df_m5 = ticker.history(period="1d", interval="5m")
        
        if df_h1.empty or df_m5.empty:
            print("❌ No Market Data")
            return

        # ២. E11 CONCEPTS: កំណត់ Session High/Low (Liquidity Zones)
        sessions = {'Tokyo': ('08:00', '10:00'), 'London': ('14:00', '16:00'), 'NY': ('19:00', '22:00')}
        sess_zones = {}
        for name, (s, e) in sessions.items():
            d = df_h1.between_time(s, e)
            sess_zones[name] = {
                'H': d['High'].max() if not d.empty else 0.0, 
                'L': d['Low'].min() if not d.empty else 0.0
            }

        # ៣. SN1P3R VOLUME DELTA: គណនាកម្លាំងទិញលក់ (CVD)
        df_m5['Delta'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
        cvd_val = df_m5['Delta'].tail(3).sum() # យក 3 candles ចុងក្រោយ (Sensitivity ខ្ពស់)
        cvd_flow = "BUYING 🟢" if cvd_val > 0 else "SELLING 🔴"

        # ៤. REPORT តាមម៉ោង (Topic 8)
        if now_kh.hour in [8, 11, 14, 16, 17, 19, 21]:
            report = (
                f"🏛 **SOVEREIGN SNIPER V12.1**\n"
                f"📅 `{now_kh.strftime('%H:%M')}` | **XAUUSD**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 **MARKET STATUS:**\n"
                f"• Price: `${df_m5['Close'].iloc[-1]:.2f}`\n"
                f"• Sn1P3r Delta: `{cvd_flow}`\n\n"
                f"🗺 **SESSION ZONES (E11):**\n"
                f"• Tokyo: `${sess_zones['Tokyo']['H']:.2f}`\n"
                f"• London: `${sess_zones['London']['H']:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 *Combo: E11 + Sn1P3r + BTrader*"
            )
            send_telegram(report, TOPIC_ANALYSIS)

        # ៥. BTRADER & E11 ALERTS: ចាប់សញ្ញា Sweep (Topic 18)
        curr_h, curr_l, curr_c = df_m5['High'].iloc[-1], df_m5['Low'].iloc[-1], df_m5['Close'].iloc[-1]
        
        for s_name, zones in sess_zones.items():
            if zones['H'] == 0: continue
            
            # $LSH (Sweep High)
            if curr_h > zones['H'] and curr_c < zones['H']:
                alert = (
                    f"🚨 **$LSH: {s_name.upper()} HIGH SWEEP**\n"
                    f"💰 Price: `${curr_c:.2f}`\n"
                    f"📊 Sn1P3r Delta: `{cvd_flow}`\n"
                    f"⚡ *Action: Watch BTrader CHoCH for SELL!*"
                )
                send_telegram(alert, TOPIC_ALERTS)
                
            # $LSL (Sweep Low)
            elif curr_l < zones['L'] and curr_c > zones['L']:
                alert = (
                    f"🚨 **$LSL: {s_name.upper()} LOW SWEEP**\n"
                    f"💰 Price: `${curr_c:.2f}`\n"
                    f"📊 Sn1P3r Delta: `{cvd_flow}`\n"
                    f"⚡ *Action: Watch BTrader CHoCH for BUY!*"
                )
                send_telegram(alert, TOPIC_ALERTS)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_system()
                              
