# Imagen base: Python 3.12 en versión ligera
FROM python:3.12-slim

# Python no guarda archivos .pyc y muestra los mensajes de la terminal al instante
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

  # Hora de Nicaragua (sin esto, el contenedor usa la hora UTC, 6 horas adelantada)
  ENV TZ=America/Managua
  RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/*

# Primero solo las librerías: así Docker no las reinstala cada vez que cambia el código
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Luego todo el proyecto
COPY . .

# Render indica el puerto en la variable PORT; en tu computadora se usa el 5000
EXPOSE 5000
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 app:app