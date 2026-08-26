import pandas as pd
from typing import Optional

def calculate_reaction(release_time_utc: pd.Timestamp, df_prices: pd.DataFrame, horizon_hours: int = 1) -> Optional[dict]:
    """
    Calcule la réaction du marché suite à une annonce économique.
    Protège strictement contre le data leakage : n'utilise jamais de données futures.
    
    Arguments:
    - release_time_utc: L'heure exacte de la publication (UTC).
    - df_prices: DataFrame contenant les prix historiques (doit avoir un index Datetime UTC).
    - horizon_hours: L'horizon d'analyse en heures (ex: 1 pour 1h, 24 pour 1 jour).
    
    Retourne:
    - Un dictionnaire avec price_before, price_after, % de changement, et la direction.
    """
    # 1. Vérifier que l'index est au bon format
    if not pd.api.types.is_datetime64_any_dtype(df_prices.index):
        df_prices.index = pd.to_datetime(df_prices.index)
        
    # 2. Trouver le prix AVANT l'annonce (Anti-Leakage)
    # On prend toutes les bougies dont l'heure de clôture est <= à l'heure de l'annonce
    past_prices = df_prices[df_prices.index <= release_time_utc]
    
    if past_prices.empty:
        # Nous n'avons pas d'historique de prix pour cette date
        return None
        
    # Le prix de référence est le "Close" de la dernière bougie connue avant l'annonce
    price_before = past_prices.iloc[-1]['Close']
    
    # 3. Trouver le prix APRES l'annonce (Horizon cible)
    target_time_utc = release_time_utc + pd.Timedelta(hours=horizon_hours)
    
    # On cherche la première bougie qui clôture APRÈS ou exactement à l'horizon cible
    future_prices = df_prices[df_prices.index >= target_time_utc]
    
    if future_prices.empty:
        # Le marché n'a pas encore atteint cet horizon (ex: annonce d'hier, horizon 7j)
        return None
        
    price_after = future_prices.iloc[0]['Close']
    
    # 4. Calcul de la performance
    pct_change = ((price_after - price_before) / price_before) * 100
    
    # Définition de la direction (ex: un mouvement de moins de 0.05% est considéré comme plat/flat)
    threshold = 0.05
    if pct_change > threshold:
        direction = "up"
    elif pct_change < -threshold:
        direction = "down"
    else:
        direction = "flat"
        
    return {
        "horizon": f"{horizon_hours}h",
        "price_before": float(price_before),
        "price_after": float(price_after),
        "pct_change": float(pct_change),
        "direction": direction
    }

if __name__ == "__main__":
    # Petit test unitaire du moteur
    print("Test du moteur statistique anti-fuite de données...")
    
    # On simule des données de prix horaires
    dates = pd.date_range(start="2023-11-01 10:00", periods=5, freq="1h", tz="UTC")
    simulated_prices = pd.DataFrame({
        "Close": [1.0500, 1.0510, 1.0550, 1.0540, 1.0580]
    }, index=dates)
    
    print("\nPrix simulés sur le marché :")
    print(simulated_prices)
    
    # On simule une annonce macro économique à 11h15 (au milieu de la bougie de 11h)
    release_date = pd.Timestamp("2023-11-01 11:15", tz="UTC")
    
    # Calcul à horizon 1h (on devrait chercher le prix vers 12h15)
    reaction = calculate_reaction(release_date, simulated_prices, horizon_hours=1)
    
    print("\nRésultat du calcul à horizon +1h pour une annonce à 11h15 :")
    print(reaction)
