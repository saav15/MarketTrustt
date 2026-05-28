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
        
        vendedores_ejemplo = [
            ("Frutería Doña María", "Selección selecta de frutas y verduras frescas con atención familiar desde 1985."),
            ("Carnicería El Torito", "Cortes premium de res, cerdo y pollo de excelente calidad e higiene garantizada."),
            ("Abarrotes San Juan", "Surtido completo de la canasta básica y productos importados a los mejores precios."),
            ("Pescadería El Puerto", "Mariscos y pescados frescos del día traídos directamente de la costa."),
            ("Verdulería La Fresca", "Verduras orgánicas, hierbas de olor y ensaladas listas para comer, 100% naturales."),
            ("Quesería Don Pepe", "Quesos artesanales, cremas y embutidos regionales de gran sabor."),
            ("Panadería La Estrella", "Pan tradicional horneado a leña caliente a toda hora, bolillos, conchas y repostería."),
            ("Pollería El Rey", "Pollo fresco cortado al gusto, limpio y con excelente trato al cliente."),
            ("Semillas El Granero", "Granos, chiles secos, especias y frutos secos a granel de excelente calidad."),
            ("Cremería Los Altos", "Lácteos de alta calidad, quesos de rancho y mantequilla pura."),
            ("Dulcería La Fiesta", "Dulces tradicionales, piñatas y botanas para todos tus eventos y antojos."),
            ("Tortillería Mexicana", "Tortillas de maíz nixtamalizado caliente al momento y masa fresca de alta calidad."),
            ("Jugos El Oasis", "Jugos naturales exprimidos al momento, licuados nutritivos y ensaladas de frutas."),
            ("Florería La Rosa", "Arreglos florales premium, plantas de ornato y flores frescas para toda ocasión."),
            ("Mariscos El Faro", "Pescados limpios, filetes frescos y los mejores camarones listos para cocinar."),
            ("Chiles El Piquín", "Variedad inmensa de chiles frescos, secos y salsas caseras de la abuela.")
        ]
        
        nombres_clientes = [
            "AnaGomez", "Luis_Perez", "CarlosM", "Sofia_R", "PedroJ", "Maria_K", "JuanP", "Carmen_L", 
            "Jorge_V", "Laura_S", "Roberto_G", "ElenaM", "Miguel_A", "Patricia_F", "Fernando_H", 
            "Lucia_D", "Alejandro_R", "Rosa_M", "Daniel_C", "Teresa_B"
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
            v_name, v_desc = vendedores_ejemplo[i]
            v_qr = str(101 + i)
            nuevo_vendedor = models.Vendor(qr_code=v_qr, name=v_name, description=v_desc)
            db.add(nuevo_vendedor)
            vendedores_creados.append(nuevo_vendedor)
        db.commit()
        
        # Asignar reseñas aleatorias a cada vendedor
        for v in vendedores_creados:
            num_reviews = random.randint(4, 9) # 4 a 9 reseñas por mercado para que haya mejores promedios
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
            "time": r.created_at.strftime("%H:%M:%S") if r.created_at else "",
            "customer_name": r.customer_name or "Anónimo"
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
            stats.append({
                "name": v.name,
                "qr": v.qr_code,
                "avg": avg,
                "count": len(reviews),
                "description": v.description or "Puesto de comida y productos del mercado tradicional."
            })
    
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

