import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # APIs y Bases de datos
    API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY") # Nueva llave para la IA gratuita
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # 🎯 FILTRO DE LIGAS (Francotirador)
    # IDs oficiales de API-Football para descargar el historial xG
    LIGAS_VIP = {
        13: "Copa Libertadores",
        11: "Copa Sudamericana",
        39: "Premier League (Inglaterra)",
        140: "La Liga (España)",
        135: "Serie A (Italia)",
        2: "Champions League"
    }

    # 🌐 FILTRO DE THE ODDS API (Para buscar cuotas en vivo hoy)
    # Comenta las ligas que no quieras escanear hoy para ahorrar créditos
    ODDS_API_LEAGUES = [
        "soccer_epl",                       # Inglaterra
        "soccer_spain_la_liga",             # España
        "soccer_italy_serie_a",             # Italia
        "soccer_conmebol_copa_libertadores",# Libertadores
        "soccer_conmebol_copa_sudamericana",# Sudamericana
        "soccer_argentina_primera_division",# Argentina
        "soccer_brazil_campeonato"          # Brasil
    ]

    # 🏛️ MAPEO DE CASAS DE APUESTAS COLOMBIANAS
    # Traducimos los proveedores globales a tus casas locales
    CASAS_ESPEJO = {
        'unibet': ['Rushbet', 'BetPlay'], # Unibet usa Kambi, igual que Rushbet y BetPlay
        'betsson': ['Betsson'],           # Betsson es global
        'williamhill': ['Wplay'],          # Espejo aproximado para cuotas de Wplay
        '1xbet': ['1xBet'],    
        'bet365': ['Bet365'],
        'bwin': ['Bwin'],
        'pinnacle': ['Pinnacle']    
    }

    # Umbral de rentabilidad mínimo para enviar alerta
    MIN_EDGE_PERCENTAGE = 10.0