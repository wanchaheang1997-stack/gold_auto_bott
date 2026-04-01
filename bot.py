import yfinance as yf
import os
import requests

# ========================================
# ⚙️ CONFIGURATION
# ========================================
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('TELEGRAM_ID')

def send_telegram(text):
    if not TOKEN or not GROUP_ID:
        print("❌ Error: Missing Secrets (TOKEN or ID)")
        return
    
    # បាញ់ត្រង់ចូល Group រួម (General) កុំទាន់ប្រើ Topic ID
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        r = requests.post(url, data=payload, timeout=15)
        print(f"Telegram Log: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Connection...")
    try:
        # ទាញតម្លៃមាសមកតេស្ត
        gold = yf.Ticker("XAUUSD=X").history(period="1d")['Close'].iloc[-1]
        msg = f"✅ **CONNECTION SUCCESS!**\n💰 តម្លៃមាសបច្ចុប្បន្ន៖ `${gold:.2f}`\n\nបើសារនេះលោតមក មានន័យថា Bot និង Telegram ស្គាល់គ្នាហើយបង!"
        send_telegram(msg)
    except:
        send_telegram("✅ **CONNECTION SUCCESS!**\nBot ដើរហើយ តែទាញតម្លៃមាសអត់ទាន់បាន។")
        
