import yfinance as yf
import pandas as pd
import numpy as np
import os, requests, pytz
from datetime import datetime

# --- កំណត់ព័ត៌មាន Telegram ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_REPORT = 8
TOPIC_ALERTS = 18

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown"}
    if topic_id: payload["message_thread_id"] = topic_id
    try:
        requests.post(url, data=payload, timeout=15)
    except: pass

# --- SMC & FVG LOGIC (LUXALGO STYLE) ---
def analyze_smc(df):
    msg_list = []
    # 1. រក Fair Value Gap (FVG)
    for i in range(len(df)-3, len(df)-1):
        c1, c2, c3 = df.iloc[i-1], df.iloc[i], df.iloc[i+1]
        if c1['High'] < c3['Low']: # Bullish FVG
            msg_list.append(f"🟢 **Bullish FVG** (${c1['High']:.2f} - ${c3['Low']:.2f})")
        if c1['Low'] > c3['High']: # Bearish FVG
            msg_list.append(f"🔴 **Bearish FVG** (${c3['High']:.2f} - ${c1['Low']:.2f})")
    
    # 2. រក Market Structure (BOS/CHoCH)
    recent_high = df['High'].iloc[-20:-2].max()
    recent_low = df['Low'].iloc[-20:-2].min()
    last_close = df['Close'].iloc[-1]
    
    structure = "Range ↔️"
    if last_close > recent_high: structure = "BOS Bullish ↗️"
    elif last_close < recent_low: structure = "BOS Bearish ↘️"
    
    return msg_list, structure

def run_sniper():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    
    # ទាញទិន្នន័យមាស និងដុល្លារ
    gold = yf.Ticker("GC=F")
    df_1h = gold.history(period="5d", interval="1h")
    df_5m = gold.history(period="1d", interval="5m")
    dxy = yf.Ticker("DX-Y.NYB").history(period="1d", interval="15m")
    
    # ភាគរយ Retailers (Simulated Sentiment)
    sentiment = "62% SHORT | 38% LONG (Contrarian: BULLISH)"
    
    # វិភាគ SMC
    fvg_alerts, structure = analyze_smc(df_5m)
    
    # --- ផ្ញើ ALERT (Topic 18) ---
    if fvg_alerts:
        alert_text = "🚨 **SNIPER ALERT: SMC SIGNALS**\n" + "\n".join(fvg_alerts)
        send_telegram(alert_text, TOPIC_ALERTS)

    # --- ផ្ញើ REPORT (Topic 8) ---
    # ផ្ញើរៀងរាល់ពេលដែល Bot រត់ក្នុងចន្លោះម៉ោង 8:00 - 22:00
    if 8 <= now.hour <= 22:
        report = (
            f"🏛 **E11 GLOBAL INTELLIGENCE V15.0**\n"
            f"⏰ `Time: {now.strftime('%H:%M')} | Price: ${df_1h['Close'].iloc[-1]:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 **1. WORLD NEWS & DRIVERS:**\n"
            f"• War/Geopolitics: High Tension Risks\n"
            f"• Central Bank: Gold Reserves Buying++\n\n"
            f"📅 **2. ECONOMIC CALENDAR:**\n"
            f"• Monitoring FED Speeches & PCE Data\n\n"
            f"👥 **3. SENTIMENTAL:**\n"
            f"`{sentiment}`\n\n"
            f"📊 **4. TECHNICAL BIAS:**\n"
            f"• Structure: `{structure}`\n"
            f"• DXY Status: {'Strong 📈' if dxy['Close'].iloc[-1] > dxy['Open'].iloc[-1] else 'Weak 📉'}\n\n"
            f"💎 **5. KEY ZONES:**\n"
            f"• PDH: `${df_1h['High'].max():.2f}`\n"
            f"• PDL: `${df_1h['Low'].min():.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Sniper, logic FVG & BOS is active!*"
        )
        send_telegram(report, TOPIC_REPORT)

if __name__ == "__main__":
    run_sniper()
    
