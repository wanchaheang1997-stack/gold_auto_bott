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
        print(f"Log: Sent to {topic_id} - Status {r.status_code}")
    except: pass

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    current_hour = now_kh.hour
    current_minute = now_kh.minute
    
    try:
        ticker = yf.Ticker("XAUUSD=X")
        df_h1 = ticker.history(period="3d", interval="1h")
        df_m5 = ticker.history(period="1d", interval="5m")
        
        if df_h1.empty or df_m5.empty: return

        # ១. SMC Logic: Session Zones (E11)
        sessions = {'Tokyo': ('08:00', '10:00'), 'London': ('14:00', '16:00'), 'NY': ('19:00', '22:00')}
        sess_zones = {}
        for name, (s, e) in sessions.items():
            d = df_h1.between_time(s, e)
            sess_zones[name] = {
                'H': d['High'].max() if not d.empty else 0.0, 
                'L': d['Low'].min() if not d.empty else 0.0
            }

        # ២. Sn1P3r Logic: Volume Delta
        df_m5['Delta'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
        cvd_val = df_m5['Delta'].tail(3).sum()
        cvd_flow = "BUYING 🟢" if cvd_val > 0 else "SELLING 🔴"
        price = df_m5['Close'].iloc[-1]

        # ៣. SCHEDULED REPORT: តាមម៉ោងដែលបងកំណត់ជាក់លាក់
        # ម៉ោង៖ 8, 10, 14, 16, 19, 21, 22
        target_hours = [8, 10, 14, 16, 19, 21, 22]
        
        # បញ្ជាក់៖ ផ្ញើតែម្តងគត់ក្នុងចន្លោះនាទីទី ០ ដល់ ១៥ នៃម៉ោងនីមួយៗ
        if current_hour in target_hours and current_minute < 15:
            report = (
                f"🏛 **SOVEREIGN REPORT V10.3.4**\n"
                f"📅 `{now_kh.strftime('%H:%M')}` | Price: `${price:.2f}`\n"
                f"📊 Sn1P3r Delta: `{cvd_flow}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🗺 **SMC ZONES (E11):**\n"
                f"• Tokyo H: `${sess_zones['Tokyo']['H']:.1f}`\n"
                f"• London H: `${sess_zones['London']['H']:.1f}`\n"
                f"• NY High: `${sess_zones['NY']['H']:.1f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 *Wait for BTrader CHoCH Confirmation*"
            )
            send_telegram(report, TOPIC_ANALYSIS)

        # ៤. STRATEGIC ALERT: Scan រក Sweep (រត់រាល់ ១៥ នាទី)
        curr_h, curr_l, curr_c = df_m5['High'].iloc[-1], df_m5['Low'].iloc[-1], df_m5['Close'].iloc[-1]
        for s_name, zones in sess_zones.items():
            if zones['H'] == 0: continue
            
            # Sweep High ($LSH)
            if curr_h > zones['H'] and curr_c < zones['H']:
                alert = f"🚨 **$LSH: {s_name} SWEEP**\n💰 Price: `${curr_c:.2f}`\n📊 Delta: `{cvd_flow}`\n⚡ *Watch CHoCH for Entry!*"
                send_telegram(alert, TOPIC_ALERTS)
                
            # Sweep Low ($LSL)
            elif curr_l < zones['L'] and curr_c > zones['L']:
                alert = f"🚨 **$LSL: {s_name} SWEEP**\n💰 Price: `${curr_c:.2f}`\n📊 Delta: `{cvd_flow}`\n⚡ *Watch CHoCH for Entry!*"
                send_telegram(alert, TOPIC_ALERTS)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_system()
        
