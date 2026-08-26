import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

def fetch_historical_prices(symbol: str, start_date: str, end_date: Optional[str] = None, interval: str = "1d") -> Optional[pd.DataFrame]:
    """
    Récupère les données historiques de prix via yfinance.
    
    Arguments:
    - symbol: Le ticker Yahoo Finance (ex: 'EURUSD=X' pour l'euro-dollar, 'GC=F' pour l'or, '^GSPC' pour le S&P 500)
    - start_date: Date de début (ex: '2023-01-01')
    - end_date: Date de fin (optionnel)
    - interval: '1d' pour journalier, '1h' pour horaire (attention, limité à ~730 jours max pour 1h sur Yahoo)
    """
    print(f"Téléchargement des données pour {symbol} (Intervalle: {interval})...")
    
    # Configuration du ticker
    ticker = yf.Ticker(symbol)
    
    # Si pas de date de fin, on prend jusqu'à aujourd'hui
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    try:
        # Téléchargement
        df = ticker.history(start=start_date, end=end_date, interval=interval)
        
        if df.empty:
            print(f"Aucune donnée trouvée pour {symbol} sur cette période.")
            return None
            
        # Nettoyage de l'index pour éviter les problèmes de timezone en base
        if df.index.tz is not None:
            df.index = df.index.tz_convert('UTC').tz_localize(None)
            
        print(f"Succès : {len(df)} bougies (chandeliers) récupérées pour {symbol}.")
        return df
        
    except Exception as e:
        print(f"Erreur lors de la récupération des prix pour {symbol} : {e}")
        return None

if __name__ == "__main__":
    # Test simple : Récupérer les 30 derniers jours de l'EUR/USD en journalier
    start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Le symbole de l'EUR/USD sur Yahoo Finance est "EURUSD=X"
    df_eurusd = fetch_historical_prices("EURUSD=X", start_date=start, interval="1d")
    
    if df_eurusd is not None and not df_eurusd.empty:
        print("\nAperçu des 3 derniers jours :")
        print(df_eurusd[['Open', 'High', 'Low', 'Close']].tail(3))
