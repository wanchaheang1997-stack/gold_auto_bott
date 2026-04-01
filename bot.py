import yfinance as yf
import pandas as pd
import numpy as np
import os
import requests
import pytz
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ========================================
# ⚙️ CONFIGURATION
# ========================================
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = 8   
TOPIC_ALERTS = 18    
TIMEZONE = "Asia/Phnom_Penh"

# ========================================
# 🛡️ SOVEREIGN ENGINE: MACRO, SENTIMENT, CALENDAR
# ========================================

def get_macro_data():
    tnx = yf.Ticker("^TNX").history(period="2d")['Close'].iloc[-1]
    gold = yf.Ticker("GC=F").history(period="2d")['Close'].iloc[-1]
    silver = yf.Ticker("SI=F").history(period="2d")['Close'].iloc[-1]
    gs_ratio = gold / silver
    return tnx, gs_ratio

def get_cvd_bias(df_m5):
    df_m5['Delta'] = np.where(df_m5['Close'] > df_m5['Open'], df_m5['Volume'], -df_m5['Volume'])
    cvd = df_m5['Delta'].tail(12).sum()
    bias = "Aggressive Buying 🟢" if cvd > 0 else "Aggressive Selling 🔴"
    return cvd, bias

def get_session_liquidity(df_h1):
    tokyo_session = df_h1.between_time('00:00', '07:00')
    if tokyo_session.empty: return None, None
    return tokyo_session['High'].max(), tokyo_session['Low'].min()

# --- [NEW] RETAIL SENTIMENT SCRAPER (Contrarian) ---
def get_fxssi_sentiment():
    """ ទាញទិន្នន័យ Sentiment ពី FXSSI (Contrarian Indicator) """
    url = "https://fxssi.com/tools/current-ratio?filter=XAUUSD"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        # រក Average Ratio (ជាទូទៅនៅខាងក្រោមគេ)
        avg_row = soup.find('div', class_='row-average')
        if avg_row:
            buy_percent = float(avg_row.find('div', class_='buy').text.strip('%'))
            sell_percent = float(avg_row.find('div', class_='sell').text.strip('%'))
            bias = "Extreme Buying ⚠️ (Look for SELL)" if buy_percent > 70 else "Extreme Selling ⚠️ (Look for BUY)" if sell_percent > 70 else "Neutral ⚖️"
            return buy_percent, sell_percent, bias
        return None, None, "Data Error"
    except:
        return None, None, "Connection Error"

# --- [NEW] ECONOMIC CALENDAR SCRAPER (Investing.com) ---
def get_investing_calendar():
    """ ទាញទិន្នន័យ News សំខាន់ៗពី Investing.com """
    url = "https://www.investing.com/economic-calendar/"
    news_list = []
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', id='economicCalendarData')
        rows = table.find_all('tr', class_='js-event-item')
        
        now_utc = datetime.utcnow()
        for row in rows:
            # យកតែ News ដែលមាន "3 Bulls" (High Impact)
            impact = row.find('td', class_='sentiment').find_all('i', class_='grayFullBullishIcon')
            if len(impact) == 3:
                time_str = row.find('td', class_='time').text.strip()
                event = row.find('td', class_='event').text.strip()
                currency = row.find('td', class_='left flagCur').text.strip()
                
                # យកតែ News របស់ USD ដែលប៉ះពាល់មាសខ្លាំង
                if currency == "USD":
                    try:
                        news_time = datetime.strptime(time_str, "%H:%M")
                        # ប្តូរម៉ោង News (ជាទូទៅ EST/EDT) មកម៉ោងខ្មែរ (ឧទាហរណ៍៖ +11h/12h អាស្រ័យរដូវ)
                        # ចំណាំ៖ នេះជាការប្តូរម៉ោងសាមញ្ញ (EDT to ICT = +11h) បងអាចប្រើ pytz ឱ្យច្បាស់ជាងនេះ
                        kh_news_time = (news_time + timedelta(hours=11)).strftime("%H:%M")
                        news_list.append(f"🕒 `{kh_news_time}` - `{event}`")
                    except: continue
        return news_list if news_list else ["No High Impact USD News today"]
    except:
        return ["Calendar Connection Error"]

def send_telegram(text, topic_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    try: requests.post(url, data=payload, timeout=15)
    except: pass

# ========================================
# 🚀 THE ALL-SEEING RUNNER (V10)
# ========================================
def run_system():
    kh_tz = pytz.timezone(TIMEZONE)
    now_kh = datetime.now(kh_tz)
    
    # 1. Fetch Core Data
    gold = yf.Ticker("GC=F")
    df_h1 = gold.history(period="5d", interval="1h")
    df_m5 = gold.history(period="2d", interval="5m")
    dxy = yf.Ticker("DX-Y.NYB").history(period="2d", interval="1h")['Close'].iloc[-1]
    
    if df_h1.empty or df_m5.empty: return

    # 2. Calculate Advanced Indicators
    yield_10y, gs_ratio = get_macro_data()
    cvd_val, cvd_bias = get_cvd_bias(df_m5)
    tokyo_h, tokyo_l = get_session_liquidity(df_h1)
    buy_per, sell_per, sent_bias = get_fxssi_sentiment()
    economic_news = get_investing_calendar()
    
    current_price = df_m5['Close'].iloc[-1]
    pdh = df_h1['High'].iloc[-24:-1].max()
    pdl = df_h1['Low'].iloc[-24:-1].min()

    # --- [A] INSTITUTIONAL MARKET REPORT (Topic 8) ---
    if now_kh.minute <= 5 and now_kh.hour in [8, 11, 14, 15, 19, 21]:
        # Fundamental: Economic Calendar
        fundamental_section = "\n".join(economic_news[:3]) # យក News ៣ ដំបូង
        
        report = (
            f"🏛 **ALL-SEEING MARKET REPORT**\n"
            f"📅 `{now_kh.strftime('%d %b %Y | %H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 **FUNDAMENTAL: Economic Calendar (USD):**\n"
            f"{fundamental_section}\n\n"
            f"📈 **MACRO DRIVERS:**\n"
            f"• US 10Y Yield: `{yield_10y:.2f}%` | DXY: `{dxy:.2f}`\n\n"
            f"🧠 **SENTIMENT (Contrarian):**\n"
            f"• Retail Ratio (XAUUSD): `Buy {buy_per:.1f}% / Sell {sell_per:.1f}%`\n"
            f"• Sentiment Bias: `{sent_bias}`\n\n"
            f"📊 **ORDER FLOW (M5):**\n"
            f"• CVD Bias: `{cvd_bias}` | Flow: `{abs(cvd_val):,.0f}`\n\n"
            f"🗺 **KEY ZONES:**\n"
            f"• Tokyo H/L: `${tokyo_h:,.1f}` / `${tokyo_l:,.1f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 *Bias: If Retail is EXTREME BUYING ⚠️, only look for SELL setups at Tokyo High.*"
        )
        send_telegram(report, TOPIC_ANALYSIS)

    # --- [B] SOVEREIGN ALERTS (Topic 18) ---
    last_m5 = df_m5.iloc[-1]
    sfp_type = None
    
    # Advanced Logic: SFP + Retail Sentiment Contrarian
    # 1. Bearish SFP (Sweep Tokyo High)
    if last_m5['High'] > tokyo_h and last_m5['Close'] < tokyo_h:
        # បើ Retail កំពុង Buy ខ្លាំង ➡️ ឱកាស Sell កាន់តែខ្ពស់ (Contrarian)
        sentiment_conf = "CONFIRMED ✅" if "Extreme Buying" in sent_bias else "Weak ⚖️"
        sfp_type = "BEARISH REVERSAL (Tokyo Sweep)"
        
    # 2. Bullish SFP (Sweep Tokyo Low)
    elif last_m5['Low'] < tokyo_l and last_m5['Close'] > tokyo_l:
        sentiment_conf = "CONFIRMED ✅" if "Extreme Selling" in sent_bias else "Weak ⚖️"
        sfp_type = "BULLISH REVERSAL (Tokyo Sweep)"

    if sfp_type:
        alert = (
            f"🚨 **SOVEREIGN SFP ALERT**\n"
            f"🎯 **Setup:** `{sfp_type}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Entry:** `${current_price:,.2f}`\n"
            f"🧠 **Retail Sent:** `{sent_bias}`\n"
            f"🏛 **Sent Conf:** `{sentiment_conf}`\n\n"
            f"📊 **CVD Flow:** `{cvd_bias}`\n"
            f"🛡 **Stop Loss:** `Above/Below SFP Wick`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Ensure M1 MSS before entry!*"
        )
        send_telegram(alert, TOPIC_ALERTS)

if __name__ == "__main__":
    run_system()
        
