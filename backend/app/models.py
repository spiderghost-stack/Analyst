from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base

class EconomicEventType(Base):
    __tablename__ = "economic_event_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country = Column(String(10), nullable=False)
    frequency = Column(String(20))
    source = Column(String(50))
    releases = relationship("EconomicRelease", back_populates="event_type")

class EconomicRelease(Base):
    __tablename__ = "economic_releases"
    id = Column(Integer, primary_key=True, index=True)
    event_type_id = Column(Integer, ForeignKey("economic_event_types.id"))
    release_datetime_utc = Column(DateTime, nullable=False)
    forecast_value = Column(Float)
    previous_value = Column(Float)
    revised_previous_value = Column(Float)
    actual_value = Column(Float)
    surprise = Column(Float)
    ingested_at = Column(DateTime, default=func.now())
    
    event_type = relationship("EconomicEventType", back_populates="releases")
    reactions = relationship("EventMarketReaction", back_populates="release")

class Instrument(Base):
    __tablename__ = "instruments"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, unique=True)
    display_name = Column(String(100))
    asset_class = Column(String(30))
    reactions = relationship("EventMarketReaction", back_populates="instrument")

class PriceData(Base):
    __tablename__ = "price_data"
    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"))
    timestamp_utc = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    timeframe = Column(String(10))

class EventMarketReaction(Base):
    __tablename__ = "event_market_reactions"
    id = Column(Integer, primary_key=True, index=True)
    release_id = Column(Integer, ForeignKey("economic_releases.id"))
    instrument_id = Column(Integer, ForeignKey("instruments.id"))
    horizon = Column(String(10), nullable=False)
    price_before = Column(Float)
    price_after = Column(Float)
    pct_change = Column(Float)
    direction = Column(String(10))
    computed_at = Column(DateTime, default=func.now())

    release = relationship("EconomicRelease", back_populates="reactions")
    instrument = relationship("Instrument", back_populates="reactions")
