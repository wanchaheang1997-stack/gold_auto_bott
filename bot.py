import requests
import os

TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = "-1003709011282"
TOPIC_ID = "8" # បន្ទប់ Analysis

def main():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID,
        "text": "📢 សួស្តីបង! នេះជាការតេស្តចេញពី GitHub ផ្ទាល់។ បើឃើញសារនេះ មានន័យថា Bot ដើរហើយ!",
        "message_thread_id": TOPIC_ID
    }
    response = requests.post(url, data=payload)
    print(response.json()) # បង្ហាញលទ្ធផលក្នុង GitHub Actions

if __name__ == "__main__":
    main()
    
