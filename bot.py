import yfinance as yf
import pandas as pd
import numpy as np
import os, requests, pytz
from datetime import datetime

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

def get_structure_1h(df):
    # រក Swing Points លើ 1H (Fractal 5)
    df['sh'] = df['High'][(df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(2)) & (df['High'] > df['High'].shift(-1)) & (df['High'] > df['High'].shift(-2))]
    df['sl'] = df['Low'][(df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(2)) & (df['Low'] < df['Low'].shift(-1)) & (df['Low'] < df['Low'].shift(-2))]
    
    last_sh = df['sh'].dropna().iloc[-1] if not df['sh'].dropna().empty else df['High'].max()
    last_sl = df['sl'].dropna().iloc[-1] if not df['sl'].dropna().empty else df['Low'].min()
    
    # Order Block 1H (Candle ចុងក្រោយមុនទម្លុះ Structure)
    ob_low = df['Low'].iloc[-2]
    ob_high = df['High'].iloc[-2]
    
    return last_sh, last_sl, ob_low, ob_high

def check_5m_confirmation(df_5m):
    # រក FVG លើ 5m សម្រាប់ Entry
    c1, c2, c3 = df_5m.iloc[-3], df_5m.iloc[-2], df_5m.iloc[-1]
    fvg_bull = c1['High'] < c3['Low']
    fvg_bear = c1['Low'] > c3['High']
    
    # រក Internal CHoCH លើ 5m (បំបែក High/Low បណ្តោះអាសន្ន)
    int_choch_bull = c3['Close'] > df_5m['High'].iloc[-6:-1].max()
    int_choch_bear = c3['Close'] < df_5m['Low'].iloc[-6:-1].min()
    
    return fvg_bull, fvg_bear, int_choch_bull, int_choch_bear

def run_sniper_v15_5():
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now = datetime.now(kh_tz)
    
    # 1. FETCH DATA
    gold = yf.Ticker("GC=F")
    df_1h = gold.history(period="5d", interval="1h")
    df_5m = gold.history(period="1d", interval="5m")
    dxy = yf.Ticker("DX-Y.NYB").history(period="1d", interval="1h")
    
    curr_p = df_5m['Close'].iloc[-1]
    
    # 2. HTF ANALYSIS (1H)
    sh_1h, sl_1h, ob_low_1h, ob_high_1h = get_structure_1h(df_1h)
    
    h1_bias = "Range ↔️"
    if curr_p > sh_1h: h1_bias = "BOS/CHoCH Bullish ↗️"
    elif curr_p < sl_1h: h1_bias = "BOS/CHoCH Bearish ↘️"

    # 3. LTF CONFIRMATION (5m)
    f_bull, f_bear, c_bull, c_bear = check_5m_confirmation(df_5m)

    # --- TOPIC 18: ALERT LOGIC (Strategy Based) ---
    # លក្ខខណ្ឌ៖ តម្លៃនៅក្នុងតំបន់ 1H OB + មាន 5m Confirmation (FVG ឬ Internal CHoCH)
    in_ob = ob_low_1h <= curr_p <= ob_high_1h
    
    if in_ob:
        if f_bull or c_bull:
            msg = f"🎯 **SNIPER BUY ENTRY (5m Confirm)**\n📍 Zone: 1H Order Block\n⚡ Confirm: {'5m FVG' if f_bull else 'Internal CHoCH'}\n💰 Price: `${curr_p:.2f}`"
            send_telegram(msg, TOPIC_ALERTS)
        elif f_bear or c_bear:
            msg = f"🎯 **SNIPER SELL ENTRY (5m Confirm)**\n📍 Zone: 1H Order Block\n⚡ Confirm: {'5m FVG' if f_bear else 'Internal CHoCH'}\n💰 Price: `${curr_p:.2f}`"
            send_telegram(msg, TOPIC_ALERTS)

    # --- TOPIC 8: REPORT LOGIC (Keep Original Style) ---
    if 8 <= now.hour <= 22:
        report = (
            f"🏛 **E11 GLOBAL INTELLIGENCE V15.5**\n"
            f"⏰ `Time: {now.strftime('%H:%M')} | Price: ${curr_p:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 **1. WORLD NEWS & DRIVERS:**\n"
            f"• War/Geopolitics: High Tension Risks\n"
            f"• Central Bank: Gold Reserves Buying++\n\n"
            f"📅 **2. ECONOMIC CALENDAR:**\n"
            f"• Monitoring FED Speeches & PCE Data\n\n"
            f"👥 **3. SENTIMENTAL:**\n"
            f"62% SHORT | 38% LONG (Contrarian: BULLISH)\n\n"
            f"📊 **4. TECHNICAL BIAS:**\n"
            f"• Structure: {h1_bias}\n"
            f"• DXY Status: {'Weak 📉' if dxy['Close'].iloc[-1] < dxy['Open'].iloc[-1] else 'Strong 📈'}\n\n"
            f"💎 **5. KEY ZONES:**\n"
            f"• PDH: `${df_1h['High'].max():.2f}`\n"
            f"• PDL: `${df_1h['Low'].min():.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Sniper, Multi-TF (1H -> 5m) is active!*"
        )
        send_telegram(report, TOPIC_REPORT)

if __name__ == "__main__":
    run_sniper_v15_5()
    
