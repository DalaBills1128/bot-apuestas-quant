import requests
from datetime import datetime, timedelta, timezone
from config import Config

class OddsFetcher:
    def __init__(self):
        self.api_key = Config.ODDS_API_KEY
        # Ligas activas y compatibles con The Odds API (incluyendo Sudamérica y Europa)
        self.ligas_activas = [
            "soccer_epl",
            "soccer_spain_la_liga",
            "soccer_italy_serie_a",
            "soccer_germany_bundesliga",
            "soccer_conmebol_copa_libertadores",
            "soccer_conmebol_copa_sudamericana",
            "soccer_argentina_primera_division",
            "soccer_brazil_campeonato"
        ]

    def obtener_cuotas_actuales(self):
        partidos_procesados = []
        limite_tiempo = datetime.now(timezone.utc) + timedelta(days=20)

        for sport_key in self.ligas_activas:
            url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
            params = {
                "api_key": self.api_key,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }

            print(f"🌐 Consultando cuotas en The Odds API para '{sport_key}'...")
            
            try:
                response = requests.get(url, params=params)
                if response.status_code != 200:
                    continue # Omitir ligas que no tengan jornada activa hoy

                eventos = response.json()

                for evento in eventos:
                    fecha_str = evento.get("commence_time")
                    fecha_partido = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    
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

        print(f"✅ Se evaluarán {len(partidos_procesados)} partidos programados para HOY en las ligas configuradas.")
        return partidos_procesados