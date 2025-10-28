import requests
import time
import threading
import os

def keep_alive():
    while True:
        try:
            url = f"https://{os.environ.get('RENDER_SERVICE_NAME')}.onrender.com/"
            response = requests.get(url)
            print(f"✅ Ping sent: {response.status_code}")
        except Exception as e:
            print(f"❌ Ping failed: {e}")
        time.sleep(300)  # Пинг каждые 5 минут

if __name__ == '__main__':
    keep_alive()
