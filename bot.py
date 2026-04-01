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

def get_realtime_calendar():
    """ទាញយកព័ត៌មានសេដ្ឋកិច្ច Real-time ពី Yahoo Finance"""
    try:
        # ទាញយកទិន្នន័យ Calendar សម្រាប់ USD ថ្ងៃនេះ
        url = "https://query1.finance.yahoo.com/v1/finance/visualization/calendar?type=economic&category=all"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        events = data.get('finance', {}).get('result', [{}])[0].get('rows', [])
        today_kh = datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d')
        
        news_list = []
        for ev in events:
            # ចម្រាញ់យកតែព័ត៌មាន USD និងមាន Impact ខ្ពស់
            if ev.get('country') == 'United States':
                e_time = ev.get('startDateTime', '').split('T')[-1][:5] # យកម៉ោង
                e_name = ev.get('event', 'N/A')
                e_impact = ev.get('importance', 'Low') # High, Medium, Low
                
                # ប្តូរម៉ោងពី UTC មក UTC+7
                utc_time = datetime.strptime(e_time, "%H:%M")
                kh_time = (utc_time + pd.Timedelta(hours=7)).strftime("%H:%M")
                
                impact_emoji = "🔴" if e_impact == 'High' else "🟡" if e_impact == 'Medium' else "⚪"
                news_list.append(f"• `{kh_time}`: {impact_emoji} {e_name}")
        
        return "\n".join(news_list[:5]) if news_list else "• No major USD news today."
    except:
        return "• ⚠️ Cannot sync live news. Check ForexFactory."

def get_macro_and_sentiment():
    try:
        gold_ticker = yf.Ticker("XAUUSD=X")
        gold_now = gold_ticker.history(period="2d")['Close'].iloc[-1]
        tnx = yf.Ticker("^TNX").history(period="2d")['Close'].iloc[-1]
        
        hist = gold_ticker.history(period="5d", interval="1h")
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        
        s_bias = "Retail Bias: BUYING 🟢" if rsi > 60 else "Retail Bias: SELLING 🔴"
        s_ratio = f"{int(rsi)}% / {100-int(rsi)}%"
        return tnx, gold_now, s_bias, s_ratio
    except: return 0.0, 0.0, "Sentiment: N/A", "50/50"

def get_session_data(df_h1):
    sessions = {'Tokyo': ('08:00', '10:00'), 'London': ('14:00', '16:00'), 'New York': ('19:00', '22:00')}
    results = {}
    for name, (start, end) in sessions.items():
        data = df_h1.between_time(start, end)
        results[name] = {'H': data['High'].max() if not data.empty else 0.0, 
                         'L': data['Low'].min() if not data.empty else 0.0}
    return results

def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=15)
    except: pass

def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    ticker = yf.Ticker("XAUUSD=X")
    df_h1 = ticker.history(period="3d", interval="1h")
    df_m5 = ticker.history(period="1d", interval="1m")
    
    if df_h1.empty or df_m5.empty: return

    tnx, gold_live, s_bias, s_ratio = get_macro_and_sentiment()
    sess = get_session_data(df_h1)
    live_news = get_realtime_calendar()
    
    df_m5['D'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
    cvd_short = df_m5['D'].tail(5).sum() 
    cvd_flow = "Sn1P3r Bias: BUYING 🟢" if cvd_short > 0 else "Sn1P3r Bias: SELLING 🔴"

    if now_kh.hour in [8, 10, 11, 14, 15, 16, 17, 19, 21]:
        report = (
            f"🏛 **SOVEREIGN V10.8 (REAL-TIME)**\n"
            f"📅 `{now_kh.strftime('%H:%M')}` | **XAUUSD**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 **LIVE ECONOMIC CALENDAR:**\n{live_news}\n\n"
            f"🧠 **SENTIMENT & VOLUME:**\n"
            f"• `{s_bias}` ({s_ratio})\n"
            f"• `{cvd_flow}` (Real-time Delta)\n"
            f"• Yield: `{tnx:.2f}%` | Price: `${gold_live:.2f}`\n\n"
            f"🗺 **SESSION LIQUIDITY:**\n"
            f"• 🇯🇵 Tokyo: `${sess['Tokyo']['H']:.1f}`\n• 🇬🇧 London: `${sess['London']['H']:.1f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Wait for Sweep + Sn1P3r Divergence*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- ALERTS ---
    curr_h, curr_l, curr_c = df_m5['High'].iloc[-1], df_m5['Low'].iloc[-1], df_m5['Close'].iloc[-1]
    for s_name, prices in sess.items():
        if prices['H'] == 0: continue
        if curr_h > prices['H'] and curr_c < prices['H']:
            send_telegram(f"🚨 **LIQUIDITY GRAB: {s_name.upper()} HIGH**\n💰 `${curr_c:,.2f}`\n📊 {cvd_flow}", TOPIC_ALERTS)
        elif curr_l < prices['L'] and curr_c > prices['L']:
            send_telegram(f"🚨 **LIQUIDITY GRAB: {s_name.upper()} LOW**\n💰 `${curr_c:,.2f}`\n📊 {cvd_flow}", TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
    
