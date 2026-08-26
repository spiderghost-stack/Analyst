import os
from typing import Any

import httpx
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

# On récupère la clé API de manière sécurisée
FRED_API_KEY = os.getenv("FRED_API_KEY")

if not FRED_API_KEY:
    raise ValueError("La variable d'environnement FRED_API_KEY est manquante dans le fichier .env")

BASE_URL = "https://api.stlouisfed.org/fred"

def fetch_series_observations(series_id: str) -> list[dict[str, Any]]:
    """
    Récupère les données historiques d'une série macroéconomique.
    Exemple: series_id = 'CPIAUCSL' pour l'inflation US (Consumer Price Index)
    """
    url = f"{BASE_URL}/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
    }
    
    response = httpx.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    return data.get("observations", [])

if __name__ == "__main__":
    # Test simple : on essaye de récupérer les derniers chiffres du CPI US
    print("Tentative de connexion à l'API FRED...")
    try:
        observations = fetch_series_observations("CPIAUCSL")
        print(f"Succès ! {len(observations)} points de données récupérés.")
        if observations:
            print(f"Dernière donnée : {observations[-1]}")
    except Exception as e:
        print(f"Erreur lors de la récupération des données : {e}")
