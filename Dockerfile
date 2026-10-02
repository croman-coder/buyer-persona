# =============================================================================
# Dockerfile para el Generador de Buyer Persona
# Pipeline batch: Google Ads + Meta Ads + Ventas → Obsidian
# =============================================================================
FROM python:3.11-slim

# Dependencias del sistema (curl para notificaciones, tzdata para zona horaria)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Zona horaria (cambiar si no estás en Asunción)
ENV TZ=America/Asuncion
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Instalar dependencias de Python primero (mejor caching de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY main.py .
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# El vault, data y .env se montan como volúmenes (ver docker-compose.yml)
# pero creamos los directorios para que existan aunque no se monten
RUN mkdir -p "Buyer Persona" data logs output

# Script de entrada
RUN chmod +x scripts/run_pipeline.sh

# Por defecto corre el pipeline una vez y sale
# Para schedule periódico, usar docker-compose con el scheduler
CMD ["python", "main.py"]