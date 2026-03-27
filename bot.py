import requests
import os
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# --- ១. ការកំណត់ (យកចេញពី GitHub Secrets) ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = os.getenv('TOPIC_ANALYSIS')
TOPIC_ALERTS = os.getenv('TOPIC_ALERTS')
HEADER_IMAGE_LINK = "ដាក់_LINK_រូបភាព_របស់_BRO_ទីនេះ"

def get_market_data():
    """ទាញយកទិន្នន័យពី Yahoo Finance ឱ្យបានគ្រប់ Timeframe"""
    try:
        gold = yf.Ticker("GC=F")
        # ទាញយកទិន្នន័យ 5m (សម្រាប់ Alerts), 1h (សម្រាប់ OB), 1d (សម្រាប់ PDH/PWH)
        df_5m = gold.history(period="3d", interval="5m")
        df_1h = gold.history(period="7d", interval="1h")
        df_1d = gold.history(period="60d", interval="1d")
        
        if df_5m.empty or df_1h.empty or df_1d.empty:
            return None, None, None
        return df_5m, df_1h, df_1d
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None, None, None

def send_telegram(text, topic_id, photo=None):
    """មុខងារផ្ញើសារ (Text ឬ Photo) ទៅកាន់ Telegram"""
    if not TOKEN or not GROUP_ID: return
    
    if photo:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        payload = {
            "chat_id": GROUP_ID, "photo": photo, "caption": text, 
            "parse_mode": "Markdown", "message_thread_id": topic_id
        }
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": GROUP_ID, "text": text, 
            "parse_mode": "Markdown", "message_thread_id": topic_id
        }
    
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def main():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now_kh = datetime.now(kh_tz)
    
    df_5m, df_1h, df_1d = get_market_data()
    if df_5m is None: return

    price = df_5m['Close'].iloc[-1]

    # --- ២. គណនា Key Levels ឱ្យបានច្បាស់លាស់ (Roadmap to A+) ---
    # External Liquidity
    pdh = df_1d['High'].iloc[-2] # ទៀនថ្ងៃម្សិលមិញ
    pdl = df_1d['Low'].iloc[-2]
    pwh = df_1d['High'].iloc[-10:-1].max() # High នៃសប្តាហ៍មុន
    pwl = df_1d['Low'].iloc[-10:-1].min()
    
    # Internal / Session Liquidity (Asia Range: 07:00 - 14:00 KH)
    asia = df_5m.between_time('00:00', '07:00') # UTC 00:00-07:00 = KH 07:00-14:00
    asia_h = asia['High'].max() if not asia.empty else None
    asia_l = asia['Low'].min() if not asia.empty else None

    # SMC Zones (Order Blocks)
    supply_ob = df_1h['High'].iloc[-48:-1].max()
    demand_ob = df_1h['Low'].iloc[-48:-1].min()

    # --- ៣. ផ្ញើ REPORT តាម SESSION (Analysis Topic) ---
    # កំណត់ម៉ោងផ្ញើ ៨ព្រឹក, ២រសៀល, ៧យប់
    if now_kh.hour in [8, 14, 19] and now_kh.minute < 10:
        session = "🌏 ASIA" if now_kh.hour == 8 else "🇪🇺 LONDON" if now_kh.hour
        
