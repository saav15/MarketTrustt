from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List
from . import models, database
import datetime

app = FastAPI(title="MarketTrust API")

# Configurar middleware de CORS para permitir orígenes cruzados en despliegue distribuido
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Crear tablas
models.Base.metadata.create_all(bind=database.engine)

def seed_database(db: Session):
    # Verificar si hay pocos vendedores, si es así, recreamos los mock data
    if db.query(models.Vendor).count() < 15:
        # Limpiar base de datos para cargar de nuevo
        db.query(models.Review).delete()
        db.query(models.Vendor).delete()
        db.commit()
        
        import random
        
        nombres_mercados = [
            "Frutería Doña María", "Carnicería El Torito", "Abarrotes San Juan", "Pescadería El Puerto",
            "Verdulería La Fresca", "Quesería Don Pepe", "Panadería La Estrella", "Pollería El Rey",
            "Semillas El Granero", "Cremería Los Altos", "Dulcería La Fiesta", "Tortillería Mexicana",
            "Jugos El Oasis", "Florería La Rosa", "Mariscos El Faro", "Chiles El Piquín"
        ]
        
        nombres_clientes = [
            "Ana", "Luis", "Carlos", "Sofia", "Pedro", "Maria", "Juan", "Carmen", 
            "Jorge", "Laura", "Roberto", "Elena", "Miguel", "Patricia", "Fernando", 
            "Lucia", "Alejandro", "Rosa", "Daniel", "Teresa"
        ]
        
        comentarios_positivos = [
            ("Todo muy fresco y excelente trato.", "Positivo", "Fresco, Excelente trato"),
            ("La mejor calidad de la ciudad.", "Positivo", "Calidad"),
            ("Precios muy justos y pesan exacto.", "Positivo", "Buen precio, Honesto"),
            ("Siempre tienen de todo, muy surtido.", "Positivo", "Surtido"),
            ("Lugar muy limpio y ordenado.", "Positivo", "Limpio, Ordenado"),
            ("Atención rápida y amable.", "Positivo", "Rápido, Amable"),
            ("Productos de primera.", "Positivo", "Alta Calidad")
        ]
        
        comentarios_negativos = [
            ("Me vendieron producto en mal estado.", "Negativo", ""),
            ("Atención lenta y de mala gana.", "Negativo", ""),
            ("Precios muy altos para la calidad.", "Negativo", ""),
            ("El local no estaba limpio.", "Negativo", ""),
            ("Me cobraron de más.", "Negativo", "")
        ]
        
        comentarios_neutrales = [
            ("Todo normal, precios estándar.", "Neutral", ""),
            ("Tienen variedad pero hay fila.", "Neutral", "Variedad"),
            ("Está bien para un apuro.", "Neutral", "")
        ]
        
        # Crear 15 vendedores
        vendedores_creados = []
        for i in range(15):
            v_name = nombres_mercados[i]
            v_qr = str(101 + i)
            nuevo_vendedor = models.Vendor(qr_code=v_qr, name=v_name)
            db.add(nuevo_vendedor)
            vendedores_creados.append(nuevo_vendedor)
        db.commit()
        
        # Asignar reseñas aleatorias a cada vendedor
        for v in vendedores_creados:
            num_reviews = random.randint(3, 8) # 3 a 8 reseñas por mercado
            for _ in range(num_reviews):
                cliente = random.choice(nombres_clientes)
                rand = random.random()
                
                # Probabilidades: 60% positivo, 25% negativo, 15% neutral
                if rand < 0.6:
                    c, sent, attr = random.choice(comentarios_positivos)
                    rating = random.randint(4, 5)
                elif rand < 0.85:
                    c, sent, attr = random.choice(comentarios_negativos)
                    rating = random.randint(1, 2)
                else:
                    c, sent, attr = random.choice(comentarios_neutrales)
                    rating = 3
                    
                db.add(models.Review(
                    vendor_id=v.id,
                    customer_name=cliente,
                    rating=rating,
                    comment=c,
                    sentiment=sent,
                    attributes=attr
                ))
        db.commit()

# Ejecutar seed localmente
db = database.SessionLocal()
seed_database(db)
db.close()

class ReviewCreate(BaseModel):
    vendor_qr: str
    customer_name: str
    rating: int
    comment: str

@app.get("/")
def read_root():
    return {"message": "Bienvenido a MarketTrust API"}

@app.post("/webhook/whatsapp")
def receive_whatsapp_review(review: ReviewCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    vendor = db.query(models.Vendor).filter(models.Vendor.qr_code == review.vendor_qr).first()
    if not vendor:
        vendor = models.Vendor(name=f"Vendedor_{review.vendor_qr}", qr_code=review.vendor_qr)
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
    
    new_review = models.Review(
        vendor_id=vendor.id,
        customer_name=review.customer_name,
        rating=review.rating,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    from .ai_brain import process_review_with_ai
    background_tasks.add_task(process_review_with_ai, new_review.id)

    return {"status": "success", "message": "Reseña recibida y procesando..."}

@app.get("/vendors/{vendor_qr}/stats")
def get_vendor_stats(vendor_qr: str, db: Session = Depends(database.get_db)):
    vendor = db.query(models.Vendor).filter(models.Vendor.qr_code == vendor_qr).first()
    if not vendor:
        return {"error": "Vendedor no encontrado"}
    
    reviews = db.query(models.Review).filter(models.Review.vendor_id == vendor.id).all()
    total_reviews = len(reviews)
    avg_rating = sum(r.rating for r in reviews) / total_reviews if total_reviews > 0 else 0
    
    all_attributes = []
    for r in reviews:
        if r.attributes:
            all_attributes.extend([attr.strip() for attr in r.attributes.split(",") if attr.strip()])
            
    from collections import Counter
    attr_counts = Counter(all_attributes)
    top_attributes = [attr for attr, count in attr_counts.most_common(3)]
    
    return {
        "vendor_name": vendor.name,
        "total_reviews": total_reviews,
        "average_rating": round(avg_rating, 2),
        "top_attributes": top_attributes
    }

@app.get("/feed")
def get_live_feed(db: Session = Depends(database.get_db)):
    reviews = db.query(models.Review, models.Vendor).join(models.Vendor, models.Review.vendor_id == models.Vendor.id).order_by(models.Review.created_at.desc()).limit(15).all()
    feed = []
    for r, v in reviews:
        feed.append({
            "id": r.id,
            "vendor_name": v.name,
            "vendor_qr": v.qr_code,
            "rating": r.rating,
            "comment": r.comment,
            "sentiment": r.sentiment or "Analizando...",
            "time": r.created_at.strftime("%H:%M:%S") if r.created_at else ""
        })
    return feed

@app.get("/leaderboard")
def get_leaderboard(db: Session = Depends(database.get_db)):
    vendors = db.query(models.Vendor).all()
    stats = []
    for v in vendors:
        reviews = db.query(models.Review).filter(models.Review.vendor_id == v.id).all()
        if reviews:
            avg = sum(r.rating for r in reviews) / len(reviews)
            stats.append({"name": v.name, "qr": v.qr_code, "avg": avg, "count": len(reviews)})
    
    # Ordenar por promedio mayor a menor
    stats.sort(key=lambda x: x["avg"], reverse=True)
    top_positive = [s for s in stats if s["avg"] >= 3.5][:4]
    
    # Ordenar por promedio menor a mayor
    stats.sort(key=lambda x: x["avg"])
    top_negative = [s for s in stats if s["avg"] < 3.5][:4]
    
    return {
        "top_positive": top_positive,
        "top_negative": top_negative
    }
