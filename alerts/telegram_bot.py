import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import Config

class NotificadorTelegram:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        
        # Configurar una sesión robusta con reintentos automáticos (Backoff Strategy)
        self.session = requests.Session()
        reintentos = Retry(
            total=5,
            backoff_factor=1,  # Espera 1s, luego 2s, luego 4s entre fallos
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adaptador = HTTPAdapter(max_retries=reintentos)
        self.session.mount("https://", adaptador)

    def enviar_alerta(self, mensaje):
        if not self.token or not self.chat_id or self.token == "tu_token_de_botfather_aqui":
            print("⚠️ Credenciales de Telegram no configuradas.")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": mensaje,
            "parse_mode": "Markdown"
        }

        try:
            # El timeout evita que el bot se quede congelado esperando respuesta
            response = self.session.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("📲 ¡Alerta enviada a Telegram con éxito!")
                return True
            else:
                print(f"❌ Error API Telegram: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Error de red severo (ej. 10054). Se agotaron los reintentos automáticos.")
            return False
        except Exception as e:
            print(f"❌ Excepción inesperada en Telegram: {e}")
            return False