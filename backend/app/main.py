from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
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
    # Verificar si hay pocos vendedores o no hay usuarios, si es así, recreamos los mock data
    if db.query(models.Vendor).count() < 16 or db.query(models.User).count() == 0:
        # Limpiar base de datos para cargar de nuevo
        db.query(models.Review).delete()
        db.query(models.Vendor).delete()
        db.query(models.User).delete()
        db.commit()
        
        import random
        
        # 1. Sembrado de Usuarios (5 Dueños y 3 Clientes)
        owner_users = []
        for i in range(5):
            new_owner = models.User(
                username=f"owner{i+1}",
                password=f"owner123", # Clave simple de prueba
                role="owner"
            )
            db.add(new_owner)
            owner_users.append(new_owner)
            
        client_users = []
        for i in range(3):
            new_client = models.User(
                username=f"client{i+1}",
                password=f"client123", # Clave simple de prueba
                role="client"
            )
            db.add(new_client)
            client_users.append(new_client)
        db.commit()
        
        # 2. Sembrado de Vendedores (16 Puestos Comerciales)
        # Google Maps Embed link para el Mercado Municipal de Tampico
        map_iframe = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3689.4449830500736!2d-97.8576402!3d22.2138936!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x85d7f7e2a9be7b79%3A0xe54e6fdab51d08e5!2sMercado%20Municipal%20de%20Tampico!5e0!3m2!1ses-419!2smx!4v1700000000000!5m2!1ses-419!2smx"
        
        vendedores_ejemplo = [
            ("Frutería Doña María", "Selección selecta de frutas y verduras frescas con atención familiar desde 1985.", 
             "https://images.unsplash.com/photo-1542838132-92c53300491e?w=600", "Calle Héroes del Cañonero #102, Zona Centro, Tampico, Tam."),
             
            ("Carnicería El Torito", "Cortes premium de res, cerdo y pollo de excelente calidad e higiene garantizada.", 
             "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=600", "Calle Fray Andrés de Olmos #204, Zona Centro, Tampico, Tam."),
             
            ("Abarrotes San Juan", "Surtido completo de la canasta básica y productos importados a los mejores precios.", 
             "https://images.unsplash.com/photo-1578916171728-46686eac8d58?w=600", "Calle Benito Juárez #305, Zona Centro, Tampico, Tam."),
             
            ("Pescadería El Puerto", "Mariscos y pescados frescos del día traídos directamente de la costa.", 
             "https://images.unsplash.com/photo-1534604973900-c43ab4c2e0ab?w=600", "Calle Cristóbal Colón #410, Zona Centro, Tampico, Tam."),
             
            ("Verdulería La Fresca", "Verduras orgánicas, hierbas de olor y ensaladas listas para comer, 100% naturales.", 
             "https://images.unsplash.com/photo-1597362925123-77861d3fbac7?w=600", "Calle Emilio Carranza #115, Zona Centro, Tampico, Tam."),
             
            ("Quesería Don Pepe", "Quesos artesanales, cremas y embutidos regionales de gran sabor.", 
             "https://images.unsplash.com/photo-1486299267070-83823f5448dd?w=600", "Calle Álvaro Obregón #512, Zona Centro, Tampico, Tam."),
             
            ("Panadería La Estrella", "Pan tradicional horneado a leña caliente a toda hora, bolillos, conchas y repostería.", 
             "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600", "Calle Venustiano Carranza #602, Zona Centro, Tampico, Tam."),
             
            ("Pollería El Rey", "Pollo fresco cortado al gusto, limpio y con excelente trato al cliente.", 
             "https://images.unsplash.com/photo-1587593817642-5999cd152795?w=600", "Calle Aduana #108, Zona Centro, Tampico, Tam."),
             
            ("Semillas El Granero", "Granos, chiles secos, especias y frutos secos a granel de excelente calidad.", 
             "https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=600", "Calle Cesar Lopez de Lara #310, Zona Centro, Tampico, Tam."),
             
            ("Cremería Los Altos", "Lácteos de alta calidad, quesos de rancho y mantequilla pura.", 
             "https://images.unsplash.com/photo-1528750901443-e9c17cc97604?w=600", "Calle Dr. Alfredo Gochicoa #205, Zona Centro, Tampico, Tam."),
             
            ("Dulcería La Fiesta", "Dulces tradicionales, piñatas y botanas para todos tus eventos y antojos.", 
             "https://images.unsplash.com/photo-1581798459219-318e76aecc7b?w=600", "Calle Sor Juana Inés de la Cruz #404, Zona Centro, Tampico, Tam."),
             
            ("Tortillería Mexicana", "Tortillas de maíz nixtamalizado caliente al momento y masa fresca de alta calidad.", 
             "https://images.unsplash.com/photo-1624300629298-e9de39c13be5?w=600", "Calle Altamira #703, Zona Centro, Tampico, Tam."),
             
            ("Jugos El Oasis", "Jugos naturales exprimidos al momento, licuados nutritivos y ensaladas de frutas.", 
             "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=600", "Calle Diaz Mirón #809, Zona Centro, Tampico, Tam."),
             
            ("Florería La Rosa", "Arreglos florales premium, plantas de ornato y flores frescas para toda ocasión.", 
             "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=600", "Calle Francisco I. Madero #111, Zona Centro, Tampico, Tam."),
             
            ("Mariscos El Faro", "Pescados limpios, filetes frescos y los mejores camarones listos para cocinar.", 
             "https://images.unsplash.com/photo-1559737113-b67439a4c276?w=600", "Calle 20 de Noviembre #222, Zona Centro, Tampico, Tam."),
             
            ("Chiles El Piquín", "Variedad inmensa de chiles frescos, secos y salsas caseras de la abuela.", 
             "https://images.unsplash.com/photo-1592417817098-8f3d6eb19675?w=600", "Calle Salvador Diaz Mirón #301, Zona Centro, Tampico, Tam.")
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
        
        # Crear 16 vendedores
        vendedores_creados = []
        for i in range(16):
            v_name, v_desc, v_img, v_addr = vendedores_ejemplo[i]
            v_qr = str(101 + i)
            # Vincular los primeros 5 puestos a nuestros 5 dueños de ejemplo
            o_id = owner_users[i].id if i < 5 else None
            
            nuevo_vendedor = models.Vendor(
                qr_code=v_qr, 
                name=v_name, 
                description=v_desc,
                image_url=v_img,
                map_address=v_addr,
                map_iframe_url=map_iframe,
                owner_id=o_id
            )
            db.add(nuevo_vendedor)
            vendedores_creados.append(nuevo_vendedor)
        db.commit()
        
        # Vincular en los modelos de usuarios dueños sus IDs de local reclamado
        for i in range(5):
            owner_users[i].claimed_vendor_id = vendedores_creados[i].id
        db.commit()
        
        # Asignar reseñas aleatorias a cada vendedor
        for v in vendedores_creados:
            num_reviews = random.randint(4, 9)
            for _ in range(num_reviews):
                cliente = random.choice(nombres_clientes)
                rand = random.random()
                
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

        # 3. Crear el vendedor especial de gala "777" (Elite, 5.0 estrellas, 40 reseñas)
        # Asignado directamente a owner1 para que tenga un local de gala reclamado
        vendedor_elite = models.Vendor(
            qr_code="777",
            name="Quesería Elite Imperial",
            description="Puesto de Gala - El estándar de oro del mercado. Especialidad en productos de alta gama y atención de realeza.",
            image_url="https://images.unsplash.com/photo-1486299267070-83823f5448dd?w=600",
            map_address="Pasillo Principal de Gala, Puesto #777, Mercado Municipal de Tampico, Tam.",
            map_iframe_url=map_iframe,
            owner_id=owner_users[0].id # Dueño 1 tiene a Quesería Elite Imperial y Frutería Doña María
        )
        db.add(vendedor_elite)
        db.commit()
        db.refresh(vendedor_elite)

        comentarios_elite = [
            "Es una experiencia mística, los quesos son de otro mundo y la atención es real.",
            "Calidad digna de reyes. Limpieza absoluta y un trato inmejorable.",
            "El mejor puesto de todo el mercado por mucho, un orgullo de la comunidad.",
            "Los productos más selectos e higiénicos. Simplemente espectacular.",
            "Atención impecable y productos de gala. Vale cada centavo.",
            "Honestidad total, báscula exacta y un sabor legendario."
        ]
        
        for i in range(40):
            cliente = f"{random.choice(nombres_clientes)}_{i+1}"
            c = random.choice(comentarios_elite)
            db.add(models.Review(
                vendor_id=vendedor_elite.id,
                customer_name=cliente,
                rating=5,
                comment=c,
                sentiment="Positivo",
                attributes="Alta Calidad, Excelente trato, Limpio, Elite"
            ))
        db.commit()

# Ejecutar seed al iniciar
db = database.SessionLocal()
seed_database(db)
db.close()

# Pydantic Schemas
class ReviewCreate(BaseModel):
    vendor_qr: str
    customer_name: str
    rating: int
    comment: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    role: str # "owner" or "client"

class VendorClaim(BaseModel):
    vendor_qr: str
    username: str

class VendorUpdate(BaseModel):
    vendor_qr: str
    description: str
    image_url: str

@app.get("/")
def read_root():
    return {"message": "Bienvenido a MarketTrust API"}

# --- ENDPOINTS DE AUTENTICACIÓN ---

@app.post("/auth/login")
def login(user_data: UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if not user or user.password != user_data.password:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    # Obtener el QR code del local reclamado si existe
    claimed_qr = None
    if user.claimed_vendor_id:
        vendor = db.query(models.Vendor).filter(models.Vendor.id == user.claimed_vendor_id).first()
        if vendor:
            claimed_qr = vendor.qr_code

    return {
        "status": "success",
        "username": user.username,
        "role": user.role,
        "claimed_vendor_id": user.claimed_vendor_id,
        "claimed_vendor_qr": claimed_qr
    }

@app.post("/auth/register")
def register(user_data: UserRegister, db: Session = Depends(database.get_db)):
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    
    new_user = models.User(
        username=user_data.username,
        password=user_data.password,
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "username": new_user.username, "role": new_user.role}

# --- ENDPOINTS DE PUESTOS / VENDEDORES ---

@app.get("/vendors/unclaimed")
def get_unclaimed_vendors(db: Session = Depends(database.get_db)):
    vendors = db.query(models.Vendor).filter(models.Vendor.owner_id == None).all()
    return [{"qr": v.qr_code, "name": v.name} for v in vendors]

@app.post("/vendors/claim")
def claim_vendor(claim_data: VendorClaim, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == claim_data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    vendor = db.query(models.Vendor).filter(models.Vendor.qr_code == claim_data.vendor_qr).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Puesto no encontrado")
        
    if vendor.owner_id is not None:
        raise HTTPException(status_code=400, detail="Este puesto ya tiene dueño")
        
    vendor.owner_id = user.id
    user.claimed_vendor_id = vendor.id
    db.commit()
    return {
        "status": "success",
        "message": f"Puesto '{vendor.name}' reclamado exitosamente",
        "claimed_vendor_qr": vendor.qr_code
    }

@app.put("/vendors/update")
def update_vendor(update_data: VendorUpdate, db: Session = Depends(database.get_db)):
    vendor = db.query(models.Vendor).filter(models.Vendor.qr_code == update_data.vendor_qr).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Puesto no encontrado")
        
    vendor.description = update_data.description
    vendor.image_url = update_data.image_url
    db.commit()
    return {"status": "success", "message": "Puesto actualizado exitosamente"}

# --- ENDPOINTS DE RESEÑAS ---

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

@app.post("/reviews/new")
def create_direct_review(review: ReviewCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    # Este endpoint realiza exactamente el mismo flujo del webhook pero sirve para la UI web de clientes
    vendor = db.query(models.Vendor).filter(models.Vendor.qr_code == review.vendor_qr).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendedor no encontrado")
        
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

    return {"status": "success", "message": "Reseña publicada con éxito"}

@app.get("/vendors")
def get_all_vendors(db: Session = Depends(database.get_db)):
    vendors = db.query(models.Vendor).all()
    return [{"qr": v.qr_code, "name": v.name} for v in vendors]

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
        "top_attributes": top_attributes,
        "image_url": vendor.image_url or "https://images.unsplash.com/photo-1542838132-92c53300491e?w=500",
        "map_address": vendor.map_address or "Zona Centro, Tampico, Tamaulipas",
        "map_iframe_url": vendor.map_iframe_url or "",
        "reviews": [{
            "customer_name": r.customer_name,
            "rating": r.rating,
            "comment": r.comment,
            "sentiment": r.sentiment or "Neutral"
        } for r in reviews]
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
