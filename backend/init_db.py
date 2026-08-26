from app.database import engine, Base
from app.models import EconomicEventType, EconomicRelease, Instrument, PriceData, EventMarketReaction
import app.models

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")
