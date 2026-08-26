"""
Script de peuplement de la base de données avec les données historiques réelles.
Ce script :
1. Crée les types d'événements (CPI, NFP, Fed)
2. Crée les instruments (EUR/USD, Or, S&P 500)
3. Récupère les données historiques depuis FRED
4. Récupère les prix historiques depuis yfinance
5. Calcule les réactions du marché pour chaque événement × instrument × horizon
"""
import os
import sys
from datetime import datetime, timedelta

import httpx
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import (
    EconomicEventType,
    EconomicRelease,
    Instrument,
    PriceData,
    EventMarketReaction,
)

load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")
FRED_BASE = "https://api.stlouisfed.org/fred"


# ============================================
# 1. Données de référence
# ============================================
EVENT_TYPES = [
    {"name": "CPI US", "country": "US", "frequency": "monthly", "source": "FRED",
     "fred_series": "CPIAUCSL"},
    {"name": "NFP US", "country": "US", "frequency": "monthly", "source": "FRED",
     "fred_series": "PAYEMS"},
    {"name": "Décision taux Fed", "country": "US", "frequency": "8x/year", "source": "FRED",
     "fred_series": "DFEDTARU"},
]

INSTRUMENTS = [
    {"symbol": "EURUSD=X", "display_name": "EUR/USD", "asset_class": "forex"},
    {"symbol": "GC=F", "display_name": "Or (Gold)", "asset_class": "commodity"},
    {"symbol": "^GSPC", "display_name": "S&P 500", "asset_class": "index"},
]

# Heures habituelles de publication (UTC)
RELEASE_HOURS = {
    "CPI US": 12,       # 8h30 ET = 12h30 UTC (heure d'été) / 13h30 UTC (heure d'hiver)
    "NFP US": 12,       # 8h30 ET
    "Décision taux Fed": 18,  # 14h00 ET
}

HORIZONS = [1, 24, 168]  # 1h, 24h, 7 jours (168h)


# ============================================
# 2. Fonctions d'ingestion
# ============================================
def fetch_fred_releases(series_id: str, start_date: str = "2015-01-01") -> list[dict]:
    """Récupère les observations historiques depuis FRED."""
    url = f"{FRED_BASE}/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
    }
    resp = httpx.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("observations", [])


def fetch_prices(symbol: str, start: str, interval: str = "1d") -> pd.DataFrame:
    """Récupère les prix historiques via yfinance."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, interval=interval)
    if df.empty:
        return df
    if df.index.tz is not None:
        df.index = df.index.tz_convert("UTC").tz_localize(None)
    return df


# ============================================
# 3. Peuplement
# ============================================
def seed_event_types(db: Session) -> dict:
    """Insère les types d'événements et retourne un mapping nom -> (id, fred_series)."""
    mapping = {}
    for et in EVENT_TYPES:
        existing = db.query(EconomicEventType).filter_by(name=et["name"]).first()
        if existing:
            mapping[et["name"]] = (existing.id, et["fred_series"])
            continue
        obj = EconomicEventType(
            name=et["name"], country=et["country"],
            frequency=et["frequency"], source=et["source"],
        )
        db.add(obj)
        db.flush()
        mapping[et["name"]] = (obj.id, et["fred_series"])
        print(f"  [+] Type d'événement créé : {et['name']}")
    db.commit()
    return mapping


def seed_instruments(db: Session) -> dict:
    """Insère les instruments et retourne un mapping symbol -> id."""
    mapping = {}
    for inst in INSTRUMENTS:
        existing = db.query(Instrument).filter_by(symbol=inst["symbol"]).first()
        if existing:
            mapping[inst["symbol"]] = existing.id
            continue
        obj = Instrument(
            symbol=inst["symbol"],
            display_name=inst["display_name"],
            asset_class=inst["asset_class"],
        )
        db.add(obj)
        db.flush()
        mapping[inst["symbol"]] = obj.id
        print(f"  [+] Instrument créé : {inst['display_name']}")
    db.commit()
    return mapping


def seed_releases(db: Session, event_types: dict):
    """Récupère les données FRED et insère les publications historiques."""
    for name, (type_id, fred_series) in event_types.items():
        existing_count = db.query(EconomicRelease).filter_by(event_type_id=type_id).count()
        if existing_count > 0:
            print(f"  [=] {name}: {existing_count} publications déjà en base, skip.")
            continue

        print(f"  [~] Téléchargement FRED pour {name} ({fred_series})...")
        observations = fetch_fred_releases(fred_series)

        if not observations:
            print(f"  [!] Aucune donnée trouvée pour {fred_series}")
            continue

        # Filtrer les observations valides (pas de ".")
        valid_obs = [o for o in observations if o["value"] != "."]
        print(f"  [~] {len(valid_obs)} observations valides trouvées")

        count = 0
        for i, obs in enumerate(valid_obs):
            date_str = obs["date"]
            actual = float(obs["value"])

            # La valeur précédente est l'observation d'avant
            previous = float(valid_obs[i - 1]["value"]) if i > 0 else None

            # Pour le MVP, on approxime le "consensus" par la valeur précédente
            # (en l'absence de données de consensus gratuites)
            forecast = previous

            # Surprise = actual - forecast
            surprise = (actual - forecast) if forecast is not None else None

            # Heure approximative de publication
            release_hour = RELEASE_HOURS.get(name, 12)
            release_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(
                hour=release_hour, minute=30
            )

            rel = EconomicRelease(
                event_type_id=type_id,
                release_datetime_utc=release_dt,
                forecast_value=forecast,
                previous_value=previous,
                actual_value=actual,
                surprise=surprise,
            )
            db.add(rel)
            count += 1

        db.commit()
        print(f"  [+] {count} publications insérées pour {name}")


def seed_prices(db: Session, instruments: dict):
    """Récupère et insère les prix historiques journaliers."""
    start_date = "2015-01-01"

    for symbol, inst_id in instruments.items():
        existing = db.query(PriceData).filter_by(instrument_id=inst_id).count()
        if existing > 0:
            print(f"  [=] {symbol}: {existing} prix déjà en base, skip.")
            continue

        print(f"  [~] Téléchargement prix pour {symbol}...")
        df = fetch_prices(symbol, start=start_date, interval="1d")

        if df.empty:
            print(f"  [!] Aucune donnée de prix pour {symbol}")
            continue

        count = 0
        for ts, row in df.iterrows():
            price = PriceData(
                instrument_id=inst_id,
                timestamp_utc=ts.to_pydatetime() if hasattr(ts, 'to_pydatetime') else ts,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                timeframe="1d",
            )
            db.add(price)
            count += 1

            # Commit par lots de 500 pour éviter les problèmes de mémoire
            if count % 500 == 0:
                db.commit()

        db.commit()
        print(f"  [+] {count} prix insérés pour {symbol}")


def compute_reactions(db: Session, event_types: dict, instruments: dict):
    """Calcule les réactions du marché pour chaque événement × instrument × horizon."""
    existing = db.query(EventMarketReaction).count()
    if existing > 0:
        print(f"  [=] {existing} réactions déjà calculées, recalcul complet...")
        db.query(EventMarketReaction).delete()
        db.commit()

    total = 0

    for name, (type_id, _) in event_types.items():
        releases = (
            db.query(EconomicRelease)
            .filter_by(event_type_id=type_id)
            .order_by(EconomicRelease.release_datetime_utc)
            .all()
        )

        for symbol, inst_id in instruments.items():
            # Charger tous les prix de cet instrument en mémoire (DataFrame)
            prices = (
                db.query(PriceData)
                .filter_by(instrument_id=inst_id, timeframe="1d")
                .order_by(PriceData.timestamp_utc)
                .all()
            )

            if not prices:
                continue

            df_prices = pd.DataFrame([{
                "timestamp": p.timestamp_utc,
                "Close": p.close,
            } for p in prices]).set_index("timestamp")

            for release in releases:
                release_time = release.release_datetime_utc

                for horizon_hours in HORIZONS:
                    # Anti-leakage : vérifier que nous avons assez de données APRÈS l'événement
                    target_time = release_time + timedelta(hours=horizon_hours)
                    if df_prices.index.max() < target_time:
                        continue  # Pas assez de données futures, on skip

                    # Prix avant
                    past = df_prices[df_prices.index <= release_time]
                    if past.empty:
                        continue
                    price_before = float(past.iloc[-1]["Close"])

                    # Prix après
                    future = df_prices[df_prices.index >= target_time]
                    if future.empty:
                        continue
                    price_after = float(future.iloc[0]["Close"])

                    # Calcul
                    pct_change = ((price_after - price_before) / price_before) * 100

                    threshold = 0.05
                    if pct_change > threshold:
                        direction = "up"
                    elif pct_change < -threshold:
                        direction = "down"
                    else:
                        direction = "flat"

                    horizon_label = {1: "1h", 24: "24h", 168: "7d"}[horizon_hours]

                    reaction = EventMarketReaction(
                        release_id=release.id,
                        instrument_id=inst_id,
                        horizon=horizon_label,
                        price_before=price_before,
                        price_after=price_after,
                        pct_change=pct_change,
                        direction=direction,
                    )
                    db.add(reaction)
                    total += 1

                    if total % 200 == 0:
                        db.commit()

        print(f"  [+] Réactions calculées pour {name}")

    db.commit()
    print(f"  [✓] Total : {total} réactions calculées et enregistrées.")


# ============================================
# Main
# ============================================
def main():
    print("=" * 60)
    print("ANALYST — Peuplement de la base de données")
    print("=" * 60)

    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("\n1/5 — Types d'événements économiques")
        event_types = seed_event_types(db)

        print("\n2/5 — Instruments financiers")
        instruments = seed_instruments(db)

        print("\n3/5 — Publications historiques (FRED)")
        seed_releases(db, event_types)

        print("\n4/5 — Prix historiques (yfinance)")
        seed_prices(db, instruments)

        print("\n5/5 — Calcul des réactions du marché (anti-leakage)")
        compute_reactions(db, event_types, instruments)

        print("\n" + "=" * 60)
        print("Peuplement terminé avec succès !")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
