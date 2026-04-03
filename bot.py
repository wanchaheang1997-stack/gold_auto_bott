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
TOPIC_REPORT = 8   
TOPIC_ALERTS = 18    
TIMEZONE = "Asia/Phnom_Penh"

def send_telegram(text, topic_id=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown"}
    if topic_id: payload["message_thread_id"] = topic_id
    try:
        requests.post(url, data=payload, timeout=15)
    except Exception as e:
        print(f"Error sending Telegram: {e}")

# --- 📊 LIQUIDITY PROFILE CALCULATION (VAH, VAL, POC) ---
def get_liquidity_profile(df, va_percent=70):
    if df.empty: return None, None, None
    price_min, price_max = df['Low'].min(), df['High'].max()
    bins = np.linspace(price_min, price_max, 31)
    v_profile = []
    for i in range(len(bins)-1):
        mask = (df['Low'] <= bins[i+1]) & (df['High'] >= bins[i])
        v_profile.append(df.loc[mask, 'Volume'].sum())
    v_profile = np.array(v_profile)
    poc_idx = np.argmax(v_profile)
    total_vol, target_vol = v_profile.sum(), v_profile.sum() * (va_percent/100)
    curr_vol, up_idx, down_idx = v_profile[poc_idx], poc_idx, poc_idx
    while curr_vol < target_vol:
        v_up = v_profile[up_idx+1] if up_idx+1 < len(v_profile) else 0
        v_down = v_profile[down_idx-1] if down_idx-1 >= 0 else 0
        if v_up >= v_down and up_idx+1 < len(v_profile):
            up_idx += 1; curr_vol += v_up
        elif down_idx-1 >= 0:
            down_idx -= 1; curr_vol += v_down
        else: break
    return bins[up_idx+1], bins[down_idx], (bins[poc_idx]+bins[poc_idx+1])/2

# --- 🚨 MULTI-TF SFP & LIQUIDITY SWEEP CHECKER ---
def check_sfp_logic(df, tf_name, levels):
    if df.empty: return
    last = df.iloc[-1]
    for name, val in levels.items():
        if val is None: continue
        # $LSL Buy Setup (Sweep ក្រោមខ្សែ Liquidity)
        if last['Low'] < val and last['Close'] > val:
            msg = f"🔥 **$LSL BUY SETUP ({tf_name})**\n📍 Sweep: {name}\n💰 Price: `${last['Close']:.2f}`"
            send_telegram(msg, TOPIC_ALERTS)
        # $LSH Sell Setup (Sweep លើខ្សែ Liquidity)
        if last['High'] > val and last['Close'] < val:
            msg = f"🔥 **$LSH SELL SETUP ({tf_name})**\n📍 Sweep: {name}\n💰 Price: `${last['Close']:.2f}`"
            send_telegram(msg, TOPIC_ALERTS)

# --- 🚀 MAIN RUNNER ---
def run_sniper_engine():
    kh_tz = pytz.timezone(TIMEZONE)
    now = datetime.now(kh_tz)
    h = now.hour

    # 1. FETCH DATA
    gold_ticker = yf.Ticker("GC=F")
    df_1h = gold_ticker.history(period="5d", interval="1h")
    df_15m = gold_ticker.history(period="2d", interval="15m")
    df_5m = gold_ticker.history(period="1d", interval="5m")
    dxy = yf.Ticker("DX-Y.NYB").history(period="1d")

    # 2. CALCULATE LEVELS
    vah, val, poc = get_liquidity_profile(df_1h)
    session_h = df_1h['High'].max()
    session_l = df_1h['Low'].min()
    
    levels = {
        "VAH (Internal)": vah, 
        "VAL (Internal)": val, 
        "POC": poc, 
        "Session High": session_h, 
        "Session Low": session_l
    }
    
    # 3. ALERT SFP (Topic 18) - ដំណើរការ ២៤ ម៉ោង
    check_sfp_logic(df_5m, "5m", levels)
    check_sfp_logic(df_15m, "15m", levels)
    check_sfp_logic(df_1h, "1h", levels)

    # 4. INTELLIGENCE REPORT (Topic 8) - ចន្លោះម៉ោង 7 AM ដល់ 10 PM
    if 7 <= h <= 22:
        daily_bias = "BULLISH 🟢" if df_1h['Close'].iloc[-1] > df_1h['Open'].iloc[-5] else "BEARISH 🔴"
        dxy_status = "Strong 📈" if not dxy.empty and dxy['Close'].iloc[-1] > dxy['Open'].iloc[-1] else "Weak 📉"
        
        report = (
            f"🏛 **E11 SOVEREIGN INTELLIGENCE**\n"
            f"⏰ `Time: {now.strftime('%H:%M')} | Price: ${df_1h['Close'].iloc[-1]:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **TECHNICAL BIAS:**\n"
            f"• 4H Structure: `Analyzing Flow`\n"
            f"• Daily Bias: `{daily_bias}`\n"
            f"• DXY Impact: `{dxy_status}`\n\n"
            f"💎 **LIQUIDITY PROFILE:**\n"
            f"• VAH: `${vah:.2f}` | VAL: `${val:.2f}`\n"
            f"• POC: `${poc:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Monitoring SFP ($LSL/$LSH) Active!*"
        )
        send_telegram(report, TOPIC_REPORT)

if __name__ == "__main__":
    run_sniper_engine()
        
