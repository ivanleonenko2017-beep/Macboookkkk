import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- ВЕБ-СЕРВЕР ДЛЯ РЕНДЕРА (чтобы не было ошибки по портам) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# Запуск веб-сервера в отдельном потоке
threading.Thread(target=run_health_check_server, daemon=True).start()

# --- ОСНОВНЫЕ НАСТРОЙКИ ---
BOT_TOKEN = "8944186419:AAEOmSyTF49UJrbDOeOjMpHWe"
CHAT_ID = "668277478"

SEARCH_URL = "https://www.olx.ua/d/uk/elektronika/noutbuki-i-accessories/noutbuki/q-macbook-air-m1/?search%5Bfilter_float_price%3Afrom%5D=13000&search%5Bfilter_float_price%3Ato%5D=16000&search%5Bstate%5D=used"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
}

seen_ids = set()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def parse_olx():
    try:
        response = requests.get(SEARCH_URL, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return

        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.find_all("div", {"data-cy": "l-card"})

        for card in cards:
            link_tag = card.find("a", href=True)
            if not link_tag:
                continue
            
            link = "https://www.olx.ua" + link_tag["href"] if link_tag["href"].startswith("/") else link_tag["href"]
            item_id = card.get("id") or link

            title_tag = card.find("h6") or card.find("h4")
            title = title_tag.text.strip() if title_tag else "MacBook Air M1"

            price_tag = card.find("p", {"data-testid": "ad-price"})
            price = price_tag.text.strip() if price_tag else "Цена не указана"

            if item_id not in seen_ids:
                if len(seen_ids) > 0:
                    message = f"🚨 <b>НОВОЕ ОБЪЯВЛЕНИЕ С МАКБУКОМ!</b>\n\n📌 <b>{title}</b>\n💰 <b>Цена:</b> {price}\n\n🔗 <a href='{link}'>Открыть на OLX</a>"
                    send_telegram_message(message)
                seen_ids.add(item_id)

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    send_telegram_message("✅ Бот мониторинга OLX успешно запущен 24/7!")
    while True:
        parse_olx()
        time.sleep(45)
