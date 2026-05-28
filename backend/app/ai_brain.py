import google.generativeai as genai
import os
import json
from . import models, database

# Configurar API Key. Prioriza variable de entorno o usa la proporcionada directamente.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBTAJJ16pjap3UxkoFrm6cGaFuX34uL30k")

genai.configure(api_key=GEMINI_API_KEY)
# Usar gemini-1.5-flash por ser rápido e ideal para tareas de extracción y clasificación
model = genai.GenerativeModel('gemini-1.5-flash')

def process_review_with_ai(review_id: int):
    """
    Función para ejecutarse en background que lee la reseña, llama a Gemini,
    y guarda el sentimiento y atributos de vuelta en la base de datos.
    """
    db = database.SessionLocal()
    try:
        review = db.query(models.Review).filter(models.Review.id == review_id).first()
        if not review or not review.comment:
            return
        
        prompt = f"""
        Actúa como un experto en análisis de sentimiento y reputación para vendedores de mercado.
        Analiza la siguiente reseña de un cliente.
        
        Reseña: "{review.comment}"
        Calificación: {review.rating} estrellas sobre 5.
        
        Debes extraer la siguiente información:
        1. 'sentiment': El sentimiento general expresado en la reseña. Escoge estrictamente UNO de esta lista: [Positivo, Negativo, Neutral, Spam]
        2. 'attributes': Extrae de 1 a 3 "Atributos de Confianza" cortos y positivos que destaquen al vendedor (ej: "Servicio amable", "Productos frescos", "Limpio"). Si la reseña es mala o spam, devuelve una lista vacía. Devuelve esto como una lista de strings.
        
        Devuelve el resultado estrictamente en formato JSON válido con las claves "sentiment" y "attributes". Sin markdown, solo el texto JSON crudo.
        """
        
        response = model.generate_content(prompt)
        
        try:
            # Limpiar posible formato markdown del JSON devuelto por Gemini
            text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            
            sentiment = data.get("sentiment", "Neutral")
            attributes_list = data.get("attributes", [])
            attributes_str = ", ".join(attributes_list)
            
            # Actualizar la base de datos
            review.sentiment = sentiment
            review.attributes = attributes_str
            db.commit()
            print(f"Reseña {review_id} procesada AI -> Sentimiento: {sentiment}, Atributos: {attributes_str}")
        except Exception as e:
            print(f"Error parseando JSON de Gemini para la reseña {review_id}: {e}\nRespuesta cruda: {response.text}")
            
    finally:
        db.close()
