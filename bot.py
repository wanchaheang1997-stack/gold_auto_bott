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
        print(f"📡 Telegram Log: Status {r.status_code}")
    except: pass

def get_binance_gold():
    # ទាញទិន្នន័យមាស (PAXG/USDT) ពី Binance ដែលដើរតួជាតម្លៃមាស Spot
    url = "https://api.binance.com/api/v3/klines"
    # ទាញទិន្នន័យ 1h
    params_h1 = {"symbol": "PAXGUSDT", "interval": "1h", "limit": 72}
    # ទាញទិន្នន័យ 5m
    params_m5 = {"symbol": "PAXGUSDT", "interval": "5m", "limit": 100}
    
    try:
        res_h1 = requests.get(url, params=params_h1).json()
        res_m5 = requests.get(url, params=params_m5).json()
        
        df_h1 = pd.DataFrame(res_h1, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime', 'QuoteAssetVol', 'Trades', 'TakerBuyBase', 'TakerBuyQuote', 'Ignore'])
        df_m5 = pd.DataFrame(res_m5, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime', 'QuoteAssetVol', 'Trades', 'TakerBuyBase', 'TakerBuyQuote', 'Ignore'])
        
        # បំប្លែងប្រភេទជួរឈរ
        for df in [df_h1, df_m5]:
            df['Time'] = pd.to_datetime(df['Time'], unit='ms').dt.tz_localize('UTC').dt.tz_convert(TIMEZONE)
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = df[col].astype(float)
        
        df_h1.set_index('Time', inplace=True)
        df_m5.set_index('Time', inplace=True)
        return df_h1, df_m5
    except Exception as e:
        print(f"❌ Binance Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    try:
        df_h1, df_m5 = get_binance_gold()
        if df_h1.empty: return

        # ១. SMC Zones (E11)
        sessions = {'Tokyo': ('08:00', '10:00'), 'London': ('14:00', '16:00'), 'NY': ('19:00', '22:00')}
        sess_zones = {}
        for name, (s, e) in sessions.items():
            d = df_h1.between_time(s, e)
            sess_zones[name] = {'H': d['High'].max() if not d.empty else 0.0, 'L': d['Low'].min() if not d.empty else 0.0}

        # ២. Sn1P3r Volume Delta
        df_m5['Delta'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
        cvd_flow = "BUYING 🟢" if df_m5['Delta'].tail(3).sum() > 0 else "SELLING 🔴"
        price = df_m5['Close'].iloc[-1]

        # ៣. Scheduled Report
        target_hours = [8, 10, 14, 16, 19, 21, 22]
        if now_kh.hour in target_hours and now_kh.minute < 15:
            report = (f"🏛 **SOVEREIGN REPORT V12.3**\n"
                      f"📅 `{now_kh.strftime('%H:%M')}` | Price: `${price:.2f}`\n"
                      f"📊 Sn1P3r Delta: `{cvd_flow}`\n"
                      f"━━━━━━━━━━━━━━━━━━━━\n"
                      f"🗺 **E11 ZONES:**\n"
                      f"• Tokyo H: `${sess_zones['Tokyo']['H']:.1f}`\n"
                      f"• London H: `${sess_zones['London']['H']:.1f}`")
            send_telegram(report, TOPIC_ANALYSIS)

        # ៤. Real-time Alert
        curr_h, curr_l, curr_c = df_m5['High'].iloc[-1], df_m5['Low'].iloc[-1], df_m5['Close'].iloc[-1]
        for s_name, zones in sess_zones.items():
            if zones['H'] == 0: continue
            if curr_h > zones['H'] and curr_c < zones['H']:
                send_telegram(f"🚨 **$LSH: {s_name} SWEEP**\n💰 Price: `${curr_c:.2f}`\n📊 Delta: `{cvd_flow}`", TOPIC_ALERTS)
            elif curr_l < zones['L'] and curr_c > zones['L']:
                send_telegram(f"🚨 **$LSL: {s_name} SWEEP**\n💰 Price: `${curr_c:.2f}`\n📊 Delta: `{cvd_flow}`", TOPIC_ALERTS)

    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    run_system()
        
