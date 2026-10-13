"""
Mide cuánto tarda cada viaje a tu base de datos (Supabase).
Uso (con el entorno virtual activado, en la carpeta del proyecto):

    python medir_latencia.py
"""
import time

from werkzeug.security import check_password_hash, generate_password_hash

from app import app, db
from sqlalchemy import text

tiempos = []
with app.app_context():
    for i in range(1, 7):
        inicio = time.perf_counter()
        db.session.execute(text("SELECT 1"))
        ms = (time.perf_counter() - inicio) * 1000
        tiempos.append(ms)
        nota = "   (la primera incluye abrir la conexión)" if i == 1 else ""
        print(f"Consulta {i}: {ms:6.0f} ms{nota}")
    db.session.rollback()

promedio = sum(tiempos[1:]) / len(tiempos[1:])
print(f"\nCada viaje a la base tarda en promedio: {promedio:.0f} ms")
if promedio < 60:
    print("→ Excelente: la distancia a la base de datos no es el problema.")
elif promedio < 150:
    print("→ Normal para una base remota. Reducir el número de viajes ayuda bastante.")
else:
    print("→ Lento: la base está lejos o la conexión es lenta. Cada viaje de más se nota mucho.")
print(f"Ejemplo: una acción de 20 viajes tardaría unos {promedio * 20 / 1000:.1f} segundos.")

# Crear una cuenta también encripta la contraseña, y eso gasta tiempo de procesador (no de red)
inicio = time.perf_counter()
hash_prueba = generate_password_hash("contrasena-de-prueba")
ms_hash = (time.perf_counter() - inicio) * 1000
inicio = time.perf_counter()
check_password_hash(hash_prueba, "contrasena-de-prueba")
ms_check = (time.perf_counter() - inicio) * 1000
print(f"\nEncriptar una contraseña (al registrarse): {ms_hash:.0f} ms")
print(f"Comprobar una contraseña (al iniciar sesión): {ms_check:.0f} ms")
if ms_hash > 500:
    print("→ Este computador tarda en encriptar: registrarse e iniciar sesión se sentirán lentos aunque la red esté bien.")
else:
    print("→ La encriptación no es el problema.")