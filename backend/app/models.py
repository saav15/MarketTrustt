from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    qr_code = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, index=True)
    customer_name = Column(String)
    rating = Column(Integer)
    comment = Column(String)
    
    # Campos que actualizará el Cerebro AI
    sentiment = Column(String, nullable=True) # Positivo, Negativo, Neutral, Spam
    attributes = Column(String, nullable=True) # Ej: "Servicio amable, Productos frescos" (separado por comas)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
