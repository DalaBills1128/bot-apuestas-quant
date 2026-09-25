import requests
from datetime import datetime, timedelta, timezone
from config import Config

class OddsFetcher:
    def __init__(self):
        self.api_key = Config.ODDS_API_KEY
        # 🎯 1. Conectamos dinámicamente a la lista que creaste en config.py
        self.ligas_activas = getattr(Config, 'ODDS_API_LEAGUES')

    def obtener_cuotas_actuales(self):
        partidos_procesados = []
        # ⏱️ 2. OPTIMIZACIÓN: Rango estricto de 24 horas para ahorrar créditos y memoria
        limite_tiempo = datetime.now(timezone.utc) + timedelta(days=2)

        for sport_key in self.ligas_activas:
            url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
            params = {
                "api_key": self.api_key,
                "regions": "eu,uk,us",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }

            print(f"🌐 Consultando cuotas en The Odds API para '{sport_key}'...")
            
            try:
                response = requests.get(url, params=params)
                
                # 🕵️ MODO ESPÍA API: Si hay un bloqueo, que lo grite en la terminal
                if response.status_code != 200:
                    print(f"⚠️ Bloqueo en '{sport_key}': Error {response.status_code} -> {response.text}")
                    continue 

                eventos = response.json()

                for evento in eventos:
                    fecha_str = evento.get("commence_time")
                    fecha_partido = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    
                    # Filtro de francotirador temporal: descartar partidos del futuro
                    if fecha_partido > limite_tiempo:
                        continue 

                    home_team = evento.get("home_team")
                    away_team = evento.get("away_team")
                    bookmakers = evento.get("bookmakers", [])

                    if not bookmakers:
                        continue

                    mercados = bookmakers[0].get("markets", [])
                    for mercado in mercados:
                        if mercado.get("key") == "h2h":
                            outcomes = mercado.get("outcomes", [])
                            cuotas = {o.get("name"): o.get("price") for o in outcomes}

                            partidos_procesados.append({
                                "local": home_team,
                                "visitante": away_team,
                                "cuota_local": cuotas.get(home_team, 0.0),
                                "cuota_empate": cuotas.get("Draw", 0.0),
                                "cuota_visitante": cuotas.get(away_team, 0.0),
                                "casa": bookmakers[0].get("title", "Mercado Global"),
                                "liga_nombre": evento.get("sport_title", "Fútbol Internacional")
                            })

            except Exception as e:
                print(f"❌ Error en The Odds API para {sport_key}: {e}")

        print(f"✅ Se evaluarán {len(partidos_procesados)} partidos programados para las próximas 48H.")
        return partidos_procesados