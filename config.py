import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # APIs
    API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
    RAPID_API_HOST = os.getenv("RAPID_API_HOST", "free-api-live-football-data.p.rapidapi.com")
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")
    
    # Dirección de la Base de Datos en la Nube (Supabase)
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Base de Datos Local (Respaldo)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "bot_apuestas_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    
    # Algoritmo Quant
    BANKROLL_INICIAL = float(os.getenv("BANKROLL_INICIAL", 100000))
    TOLERANCIA_CUOTA = float(os.getenv("TOLERANCIA_CUOTA", 0.10))
    FRACCION_KELLY = float(os.getenv("FRACCION_KELLY", 0.25))

if __name__ == "__main__":
    print("Configuración cargada correctamente.")