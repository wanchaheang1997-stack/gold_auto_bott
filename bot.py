import requests
import os
import yfinance as yf
from datetime import datetime
import pytz

# --- Configuration ពី GitHub Secrets ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')
TOPIC_ANALYSIS = os.getenv('TOPIC_ANALYSIS')
TOPIC_ALERTS = os.getenv('TOPIC_ALERTS')

def get_smc_data():
    try:
        gold = yf.Ticker("GC=F")
        # ទាញយកទិន្នន័យ Hourly ដើម្បីរក PDH/PDL និង Swing
        df = gold.history(period="5d", interval="1h")
        if df.empty: return None

        # 1. Previous Day High/Low (PDH/PDL)
        # យកទិន្នន័យ ២៤ ទៀនចុងក្រោយ (មិនរាប់ទៀនបច្ចុប្បន្ន)
        pdh = df['High'].iloc[-25:-1].max()
        pdl = df['Low'].iloc[-25:-1].min()

        # 2. Asia Session Range (00:00 - 08:00 UTC)
        asia_data = df.between_time('00:00', '08:00')
        asia_high = asia_data['High'].max() if not asia_data.empty else pdh
        asia_low = asia_data['Low'].min() if not asia_data.empty else pdl

        # 3. Order Block (រកមើល Swing High/Low ចុងក្រោយ)
        supply_ob = df['High'].iloc[-48:-1].max()
        demand_ob = df['Low'].iloc[-48:-1].min()

        return {
            "price": df['Close'].iloc[-1],
            "pdh": pdh,
            "pdl": pdl,
            "asia_high": asia_high,
            "asia_low": asia_low,
            "supply_ob": supply_ob,
            "demand_ob": demand_ob,
            "pct": ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

def send_msg(text, topic_id):
    if not topic_id: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "Markdown", "message_thread_id": topic_id}
    requests.post(url, data=payload)

def main():
    data = get_smc_data()
    if not data: return
    
    price = data['price']
    kh_tz = pytz.timezone("Asia/Phnom_Penh")
    now_kh = datetime.now(kh_tz)
    
    # --- ១. ផ្ញើ REPORT តាម SESSION (8, 14, 19) ---
    if now_kh.hour in [8, 14, 19] and now_kh.minute < 15:
        session = "🌏 ASIA" if now_kh.hour == 8 else "🇪🇺 LONDON" if now_kh.hour == 14 else "🇺🇸 NEW YORK"
        report = (
            f"📊 **{session} SESSION | SMC MAP**\n"
            f"📅 `{now_kh.strftime('%d/%m/%Y | %H:%M')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 **Current Price:** `${price:,.2f}`\n\n"
            f"🛑 **LIQUIDITY LEVELS**\n"
            f"• PDH (Prev. Day High): `${data['pdh']:,.2f}`\n"
            f"• PDL (Prev. Day Low): `${data['pdl']:,.2f}`\n"
            f"• Asia High: `${data['asia_high']:,.2f}`\n"
            f"• Asia Low: `${data['asia_low']:,.2f}`\n\n"
            f"🧱 **SMC ZONES (OB)**\n"
            f"• Supply OB: `${data['supply_ob']:,.2f}`\n"
            f"• Demand OB: `${data['demand_ob']:,.2f}`\n\n"
            f"⚡ **Bias:** {'🟢 Bullish' if data['pct'] > 0 else '🔴 Bearish'}"
        )
        send_msg(report, TOPIC_ANALYSIS)

    # --- ២. ប្រព័ន្ធ ALERT LIQUIDITY SWEEP (រត់រាល់ ១៥ នាទី) ---
    # ប្រាប់ពេលតម្លៃបំបែក PDH (Buyside Liquidity Taken)
    if price > data['pdh']:
        alert = f"🚨 **LIQUIDITY ALERT: PDH SWEEP!**\nPrice is above Yesterday's High: `${price:,.2f}`\n*មើលសញ្ញា Reversal (Short) នៅតំបន់ Supply!*"
        send_msg(alert, TOPIC_ALERTS)
    
    # ប្រាប់ពេលតម្លៃបំបែក PDL (Sellside Liquidity Taken)
    elif price < data['pdl']:
        alert = f"🚨 **LIQUIDITY ALERT: PDL SWEEP!**\nPrice is below Yesterday's Low: `${price:,.2f}`\n*មើលសញ្ញា Reversal (Long) នៅតំបន់ Demand!*"
        send_msg(alert, TOPIC_ALERTS)

if __name__ == "__main__":
    main()
        
