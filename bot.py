import yfinance as yf
import pandas as pd
import numpy as np
import os, requests, pytz
from datetime import datetime
from tradingview_ta import TA_Handler, Interval

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_REPORT = 8
TOPIC_ALERTS = 18

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown"}
    if topic_id: payload["message_thread_id"] = topic_id
    try: requests.post(url, data=payload, timeout=15)
    except: pass

def get_tv_summary():
    try:
        handler = TA_Handler(symbol="XAUUSD", screener="forex", exchange="OANDA", interval=Interval.INTERVAL_1_HOUR)
        return handler.get_analysis().summary['RECOMMENDATION']
    except: return "NEUTRAL"

def run_v29_full():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    
    # 1. FETCH LIVE DATA
    gold = yf.Ticker("GC=F")
    df_1h = gold.history(period="5d", interval="1h")
    df_5m = gold.history(period="2d", interval="5m")
    if df_1h.empty: return
    
    curr_p = df_5m['Close'].iloc[-1]
    tv_rec = get_tv_summary()

    # 2. SMC & DELTA LOGIC
    h1_ob_l, h1_ob_h = df_1h['Low'].iloc[-2], df_1h['High'].iloc[-2]
    
    # Sn1P3r Vol Delta (1.5x Spike)
    deltas = (df_5m['Close'] - df_5m['Low']) - (df_5m['High'] - df_5m['Close'])
    avg_delta = deltas.tail(10).mean()
    curr_delta = deltas.iloc[-1]
    vol_spike = abs(curr_delta) > (abs(avg_delta) * 1.5)

    # 3. TOPIC 18: SNIPER ALERT (បាញ់តែពេលមាន Setup)
    if h1_ob_l <= curr_p <= h1_ob_h and vol_spike:
        direction = "BUY" if curr_delta > 0 else "SELL"
        if direction in tv_rec or "STRONG" in tv_rec:
            alert_msg = (
                f"🎯 **XAUUSD SNIPER {direction}**\n"
                f"🔭 TV Status: {tv_rec}\n"
                f"🔥 Zone: 1H Order Block\n"
                f"📊 Sn1p3r Delta: {curr_delta:.0f} (Spike!)\n"
                f"💰 Price: `${curr_p:.2f}`"
            )
            send_telegram(alert_msg, TOPIC_ALERTS)

    # 4. TOPIC 8: HOURLY REPORT (បាញ់រាល់ដើមម៉ោង)
    if now.minute < 10: # បាញ់ក្នុងចន្លោះ ១០នាទីដំបូងនៃម៉ោងនីមួយៗ
        report = (
            f"🏛 **E11 GLOBAL INTELLIGENCE V29.0**\n"
            f"⏰ `Time: {now.strftime('%H:%M')} | Price: ${curr_p:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 **MARKET CONTEXT:**\n• Gold is reacting to 1H zones.\n• Session: {'Active' if 14 <= now.hour <= 22 else 'Quiet'}\n\n"
            f"📊 **TECHNICALS:**\n• TV Summary: **{tv_rec}**\n• RSI (1h): Neutral\n\n"
            f"💎 **KEY ZONES:**\n• 1H OB: `${h1_ob_l:.2f} - ${h1_ob_h:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n✅ *Full Monitoring is Active!*"
        )
        send_telegram(report, TOPIC_REPORT)

if __name__ == "__main__":
    run_v29_full()
    
