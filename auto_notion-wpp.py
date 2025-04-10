import requests
import time
import os
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

load_dotenv()

NOTION_SECRET = os.getenv("NOTION_SECRET")
DATABASE_ID = os.getenv("DATABASE_ID")
NOTION_URL = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
HEADERS = {
    "Authorization": f"Bearer {NOTION_SECRET}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TO_PHONE = os.getenv("TO_PHONE")

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

def get_notion_data():
    response = requests.post(NOTION_URL, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro: {response.status_code} - {response.text}")
        return None

def send_whatsapp_message(msg):
    message = client.messages.create(
        from_=TWILIO_FROM,
        body=msg,
        to=TO_PHONE
    )
    print(f"Mensagem enviada! ID: {message.sid}")

notified_pages = set()

def monitor_notion():
    data = get_notion_data()
    if data:
        today = datetime.today().strftime("%Y-%m-%d") 

        for page in data["results"]:
            properties = page["properties"]
            page_id = page["id"]
            notion_date = properties.get("Prox Rev", {}).get("date", {})
            conteudo = properties.get("Conteudo", {}).get("title", [{}])[0].get("text", {}).get("content", "Conteúdo não disponível")

            if notion_date:
                notion_date_str = notion_date.get("start", "")
                if notion_date_str == today and page_id not in notified_pages:
                    msg = f"Lembrete: Revisar Conteúdo: {conteudo} hoje!"
                    send_whatsapp_message(msg)
                    notified_pages.add(page_id)


scheduler = BackgroundScheduler()
scheduler.add_job(monitor_notion, 'interval', seconds=30)
scheduler.start()

@app.route('/')
def index():
    return "Servidor está funcionando!"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
