import requests
from config import Config

def ver_ligas():
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={Config.ODDS_API_KEY}"
    resp = requests.get(url)
    
    if resp.status_code == 200:
        deportes = resp.json()
        print("⚽ Ligas de fútbol disponibles en tu plan de The Odds API:\n")
        for d in deportes:
            if "colombia" in d.get("key", "").lower() or "soccer_" in d.get("key", "").lower():
                print(f"Clave: '{d['key']}'  --->  Nombre: {d['title']}")
    else:
        print("Error consultando The Odds API")

if __name__ == "__main__":
    ver_ligas()