from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Usamos SQLite guardando el archivo en /app/data que será un volumen de Docker
DATABASE_URL = "sqlite:////app/data/markettrust.db"

# En caso de que se ejecute localmente sin Docker, aseguramos que exista
os.makedirs("/app/data", exist_ok=True)
# Alternativa para local dev: 
# DATABASE_URL = "sqlite:///./markettrust.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
