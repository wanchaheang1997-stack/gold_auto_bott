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

def get_tv_data():
    # ទាញទិន្នន័យវិភាគផ្ទាល់ពី TradingView
    try:
        handler = TA_Handler(
            symbol="XAUUSD",
            screener="forex",
            exchange="OANDA",
            interval=Interval.INTERVAL_5_MINUTES
        )
        return handler.get_analysis()
    except: return None

def run_v26_hybrid():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    
    # 1. PREREQUISITES: មិនបាញ់ Alert ម៉ោង Asian Session (07:00-14:00 KH)
    if now.weekday() >= 5 or (7 <= now.hour < 14):
        return

    # 2. FETCH DATA (Yahoo Finance & TradingView)
    gold = yf.Ticker("GC=F")
    df_d1 = gold.history(period="200d", interval="1d")
    df_1h = gold.history(period="10d", interval="1h")
    df_5m = gold.history(period="2d", interval="5m")
    tv_analysis = get_tv_data()
    
    if df_5m.empty or tv_analysis is None: return
    curr_p = df_5m['Close'].iloc[-1]

    # 3. TRADINGVIEW CONFIRMATION (V.21 Logic)
    tv_rec = tv_analysis.summary['RECOMMENDATION'] # "STRONG_BUY", "BUY", etc.
    tv_rsi = tv_analysis.indicators["RSI"]

    # 4. SNIPER LOGIC (V.25 Logic)
    # Daily Bias (EMA 200)
    ema200_d1 = df_d1['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
    d1_bias = "BUY" if curr_p > ema200_d1 else "SELL"

    # 1H Order Block (SMC)
    h1_low, h1_high = df_1h['Low'].iloc[-2], df_1h['High'].iloc[-2]
    in_1h_zone = h1_low <= curr_p <= h1_high

    # Sn1P3r Volume Delta (1.5x Spike)
    deltas = (df_5m['Close'] - df_5m['Low']) - (df_5m['High'] - df_5m['Close'])
    avg_delta = deltas.tail(10).mean()
    curr_delta = deltas.iloc[-1]
    vol_spike = abs(curr_delta) > (abs(avg_delta) * 1.5)

    # 5. HYBRID TRIGGER (Combined Force)
    if in_1h_zone and vol_spike:
        # BUY: D1 Up + TV Buy + Delta Spike Up
        if d1_bias == "BUY" and "BUY" in tv_rec and curr_delta > 0:
            msg = (f"🎯 **XAUUSD HYBRID SNIPER: BUY**\n"
                   f"🔭 TV Status: {tv_rec} | RSI: {tv_rsi:.1f}\n"
                   f"🔥 Zone: 1H Order Block\n"
                   f"📊 Delta Spike: {curr_delta:.0f} (1.5x)\n"
                   f"💰 Price: `${curr_p:.2f}`")
            send_telegram(msg, TOPIC_ALERTS)
            
        # SELL: D1 Down + TV Sell + Delta Spike Down
        elif d1_bias == "SELL" and "SELL" in tv_rec and curr_delta < 0:
            msg = (f"🎯 **XAUUSD HYBRID SNIPER: SELL**\n"
                   f"🔭 TV Status: {tv_rec} | RSI: {tv_rsi:.1f}\n"
                   f"🔥 Zone: 1H Order Block\n"
                   f"📊 Delta Spike: {curr_delta:.0f} (1.5x)\n"
                   f"💰 Price: `${curr_p:.2f}`")
            send_telegram(msg, TOPIC_ALERTS)

    # 6. HOURLY REPORT (Topic 8)
    if 8 <= now.hour <= 22 and now.minute < 5:
        report = (
            f"🏛 **E11 HYBRID INTELLIGENCE V26.0**\n"
            f"⏰ `Time: {now.strftime('%H:%M')} | Price: ${curr_p:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **1. TRADINGVIEW SUMMARY:**\n• Signal: **{tv_rec}**\n• RSI (5m): {tv_rsi:.2f}\n\n"
            f"📈 **2. DAILY BIAS:**\n• Trend: {d1_bias} (vs EMA 200)\n\n"
            f"💎 **3. SMC ZONES:**\n• 1H OB: `${h1_low:.2f} - ${h1_high:.2f}`\n\n"
            f"✅ *Alignment: {'YES' if d1_bias in tv_rec else 'NO'}*"
        )
        send_telegram(report, TOPIC_REPORT)

if __name__ == "__main__":
    run_v26_hybrid()
    
