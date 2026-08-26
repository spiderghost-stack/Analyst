"""
ANALYST — API FastAPI
Sert les données statistiques au frontend.
"""
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models import (
    EconomicEventType,
    EconomicRelease,
    Instrument,
    EventMarketReaction,
)

# Créer les tables si besoin
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Analyst API", version="1.0.0")

# CORS : autoriser le frontend (localhost:5173) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# Schémas Pydantic (réponses typées)
# ============================================
class EventOut(BaseModel):
    id: int
    name: str
    country: str
    frequency: str | None
    datetime_utc: str
    importance: str
    last_actual: float | None
    last_forecast: float | None
    last_surprise: float | None


class HorizonStat(BaseModel):
    direction: str
    pct: float
    sample: int
    avg_move: float


class InstrumentStat(BaseModel):
    name: str
    symbol: str
    horizons: dict[str, HorizonStat]


class ExplanationOut(BaseModel):
    text_before: str
    sample: int
    text_condition: str
    instrument: str
    direction: str
    direction_class: str
    horizon: str
    count: int
    pct: float


class DistributionBucket(BaseModel):
    range: str
    count: int
    direction: str


class EventStatsOut(BaseModel):
    instruments: list[InstrumentStat]
    distribution: list[DistributionBucket]
    explanation: ExplanationOut


# ============================================
# Endpoints
# ============================================
@app.get("/api/events", response_model=list[EventOut])
def get_events(db: Session = Depends(get_db)):
    """Liste tous les types d'événements avec leur dernière publication."""
    event_types = db.query(EconomicEventType).all()
    results = []

    for et in event_types:
        # Dernière publication connue
        last_release = (
            db.query(EconomicRelease)
            .filter_by(event_type_id=et.id)
            .order_by(EconomicRelease.release_datetime_utc.desc())
            .first()
        )

        # Prochaine date estimée (approximation basée sur la fréquence)
        if last_release:
            if et.frequency == "monthly":
                next_dt = last_release.release_datetime_utc + timedelta(days=30)
            else:
                next_dt = last_release.release_datetime_utc + timedelta(days=45)
        else:
            next_dt = datetime.utcnow()

        # Importance (tous high pour le MVP)
        importance = "high"

        results.append(EventOut(
            id=et.id,
            name=et.name,
            country=et.country,
            frequency=et.frequency,
            datetime_utc=next_dt.isoformat() + "Z",
            importance=importance,
            last_actual=last_release.actual_value if last_release else None,
            last_forecast=last_release.forecast_value if last_release else None,
            last_surprise=last_release.surprise if last_release else None,
        ))

    return results


@app.get("/api/events/{event_type_id}/stats", response_model=EventStatsOut)
def get_event_stats(event_type_id: int, db: Session = Depends(get_db)):
    """
    Calcule les statistiques historiques pour un type d'événement donné.
    Retourne les probabilités par instrument × horizon, la distribution, et l'explication.
    """
    event_type = db.query(EconomicEventType).get(event_type_id)
    instruments = db.query(Instrument).all()

    # Récupérer toutes les publications pour ce type d'événement
    releases = (
        db.query(EconomicRelease)
        .filter_by(event_type_id=event_type_id)
        .all()
    )
    release_ids = [r.id for r in releases]

    # Récupérer toutes les réactions liées
    reactions = (
        db.query(EventMarketReaction)
        .filter(EventMarketReaction.release_id.in_(release_ids))
        .all()
    )

    # Organiser les réactions par instrument et horizon
    # Structure : {instrument_id: {horizon: [reactions]}}
    reactions_map = defaultdict(lambda: defaultdict(list))
    for r in reactions:
        reactions_map[r.instrument_id][r.horizon].append(r)

    instrument_stats = []
    best_stat = None  # Pour l'explication pédagogique

    for inst in instruments:
        horizons_data = {}
        for horizon in ["1h", "24h", "7d"]:
            horizon_reactions = reactions_map[inst.id][horizon]
            sample = len(horizon_reactions)

            if sample == 0:
                horizons_data[horizon] = HorizonStat(
                    direction="flat", pct=50.0, sample=0, avg_move=0.0
                )
                continue

            up_count = sum(1 for r in horizon_reactions if r.direction == "up")
            down_count = sum(1 for r in horizon_reactions if r.direction == "down")
            avg_move = sum(r.pct_change for r in horizon_reactions) / sample

            if up_count >= down_count:
                direction = "up"
                pct = (up_count / sample) * 100
            else:
                direction = "down"
                pct = (down_count / sample) * 100

            stat = HorizonStat(
                direction=direction,
                pct=round(pct, 1),
                sample=sample,
                avg_move=round(avg_move, 2),
            )
            horizons_data[horizon] = stat

            # Garder la meilleure stat (1h, plus grand échantillon) pour l'explication
            if horizon == "1h" and (best_stat is None or sample > best_stat["sample"]):
                best_stat = {
                    "instrument": inst.display_name,
                    "direction": "baissé" if direction == "down" else "monté",
                    "direction_class": direction,
                    "count": down_count if direction == "down" else up_count,
                    "pct": round(pct, 1),
                    "sample": sample,
                }

        instrument_stats.append(InstrumentStat(
            name=inst.display_name,
            symbol=inst.symbol,
            horizons=horizons_data,
        ))

    # Distribution des réactions (EUR/USD, 1h par défaut)
    first_inst = instruments[0] if instruments else None
    distribution_reactions = reactions_map[first_inst.id]["1h"] if first_inst else []

    buckets = [
        {"range": "< -1%", "min": -999, "max": -1},
        {"range": "-1% à -0.5%", "min": -1, "max": -0.5},
        {"range": "-0.5% à -0.2%", "min": -0.5, "max": -0.2},
        {"range": "-0.2% à 0%", "min": -0.2, "max": 0},
        {"range": "0% à +0.2%", "min": 0, "max": 0.2},
        {"range": "+0.2% à +0.5%", "min": 0.2, "max": 0.5},
        {"range": "+0.5% à +1%", "min": 0.5, "max": 1},
        {"range": "> +1%", "min": 1, "max": 999},
    ]

    distribution = []
    for b in buckets:
        count = sum(
            1 for r in distribution_reactions
            if b["min"] <= r.pct_change < b["max"]
        )
        distribution.append(DistributionBucket(
            range=b["range"],
            count=count,
            direction="down" if b["max"] <= 0 else "up",
        ))

    # Explication pédagogique
    event_name_map = {
        "CPI US": "publications du CPI US (inflation)",
        "NFP US": "publications du NFP US (emploi)",
        "Décision taux Fed": "décisions de taux de la Fed",
    }
    condition_text = event_name_map.get(event_type.name, f"publications de {event_type.name}")

    if best_stat is None:
        best_stat = {
            "instrument": "EUR/USD",
            "direction": "évolué",
            "direction_class": "flat",
            "count": 0,
            "pct": 50.0,
            "sample": 0,
        }

    explanation = ExplanationOut(
        text_before="Sur",
        sample=best_stat["sample"],
        text_condition=f"{condition_text} depuis 2015",
        instrument=best_stat["instrument"],
        direction=best_stat["direction"],
        direction_class=best_stat["direction_class"],
        horizon="l'heure suivante",
        count=best_stat["count"],
        pct=best_stat["pct"],
    )

    return EventStatsOut(
        instruments=instrument_stats,
        distribution=distribution,
        explanation=explanation,
    )
