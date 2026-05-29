FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto de la aplicación
EXPOSE 8000

# Comando para ejecutar Uvicorn dinámicamente según el puerto asignado por Railway ($PORT), por defecto 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

