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
GROUP_ID = os.getenv('TELEGRAM_ID') # -1003709011282
TOPIC_ANALYSIS = 8   
TOPIC_ALERTS = 18    
TIMEZONE = "Asia/Phnom_Penh"

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown"}
    if topic_id: payload["message_thread_id"] = topic_id
    try:
        r = requests.post(url, data=payload, timeout=15)
        print(f"Log Status: {r.status_code}")
    except: pass

def get_data_stable():
    # ប្រើ Binance API ជំនួស Yahoo ដើម្បីកុំឱ្យគាំង
    url = "https://api.binance.com/api/v3/klines"
    try:
        # ទាញ PAXG (Gold) 1h សម្រាប់ Zones
        res_h1 = requests.get(url, params={"symbol": "PAXGUSDT", "interval": "1h", "limit": 100}).json()
        df_h1 = pd.DataFrame(res_h1, columns=['Time','O','H','L','C','V','CT','QV','T','TB','TQ','I'])
        # ទាញ 5m សម្រាប់ Alert
        res_m5 = requests.get(url, params={"symbol": "PAXGUSDT", "interval": "5m", "limit": 100}).json()
        df_m5 = pd.DataFrame(res_m5, columns=['Time','O','H','L','C','V','CT','QV','T','TB','TQ','I'])
        
        for df in [df_h1, df_m5]:
            df['Time'] = pd.to_datetime(df['Time'], unit='ms').dt.tz_localize('UTC').dt.tz_convert(TIMEZONE)
            for col in ['O','H','L','C','V']: df[col] = df[col].astype(float)
        
        df_h1.set_index('Time', inplace=True)
        df_m5.set_index('Time', inplace=True)
        return df_h1, df_m5
    except: return pd.DataFrame(), pd.DataFrame()

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    df_h1, df_m5 = get_data_stable()
    if df_h1.empty: return

    # ១. គណនា Session Zones (E11)
    sessions = {'Tokyo': ('08:00', '10:00'), 'London': ('14:00', '16:00'), 'NY': ('19:00', '22:00')}
    zones = {}
    for s_name, (start, end) in sessions.items():
        d = df_h1.between_time(start, end)
        zones[s_name] = {'H': d['H'].max() if not d.empty else 0, 'L': d['L'].min() if not d.empty else 0}

    # ២. Sn1P3r Logic
    df_m5['Delta'] = np.where(df_m5['C'] > df_m5['O'], df_m5['V'], -df_m5['V'])
    cvd_flow = "Aggressive Buying 🟢" if df_m5['Delta'].tail(5).sum() > 0 else "Aggressive Selling 🔴"
    price = df_m5['C'].iloc[-1]

    # ៣. ផ្ញើ Report តាមម៉ោង (8, 10, 14, 16, 19, 21, 22)
    if now_kh.hour in [8, 10, 14, 16, 19, 21, 22] and now_kh.minute < 15:
        report = (
            f"🏛 **SOVEREIGN SESSION REPORT**\n"
            f"📅 `{now_kh.strftime('%H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 **MACRO & SENTIMENT:**\n"
            f"• Price: `${price:.2f}`\n"
            f"• CVD: `{cvd_flow}`\n\n"
            f"🗺 **SESSION ZONES (UTC+7):**\n"
            f"• 🇯🇵 Tokyo: `${zones['Tokyo']['L']:.1f}` - `${zones['Tokyo']['H']:.1f}`\n"
            f"• 🇬🇧 London: `${zones['London']['L']:.1f}` - `${zones['London']['H']:.1f}`\n"
            f"• 🇺🇸 N.York: `${zones['NY']['L']:.1f}` - `${zones['NY']['H']:.1f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Check SFP at these Levels!*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # ៤. Alert Real-time (រត់រាល់ ១៥ នាទី)
    curr_h, curr_l, curr_c = df_m5['H'].iloc[-1], df_m5['L'].iloc[-1], df_m5['C'].iloc[-1]
    for s_name, z in zones.items():
        if z['H'] == 0: continue
        if curr_h > z['H'] and curr_c < z['H']:
            send_telegram(f"🚨 **$LSH: {s_name} Sweep High**\n💰 Price: `${curr_c:.2f}`\n📊 CVD: `{cvd_flow}`", TOPIC_ALERTS)
        elif curr_l < z['L'] and curr_c > z['L']:
            send_telegram(f"🚨 **$LSL: {s_name} Sweep Low**\n💰 Price: `${curr_c:.2f}`\n📊 CVD: `{cvd_flow}`", TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
    
