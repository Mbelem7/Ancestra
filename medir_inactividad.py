"""
Comprueba si la conexión a Supabase se "duerme" cuando pasa un rato sin usarla.
Uso (con el entorno virtual activado, en la carpeta del proyecto):

    python medir_inactividad.py

Tarda unos 2 minutos y medio, porque espera 20, 45 y 75 segundos sin usar la base de datos.
Lo normal es que cada consulta después de la espera tarde menos de 1 segundo.
"""
import time

from app import app, db
from sqlalchemy import text

ESPERAS = (20, 45, 75)   # segundos sin usar la base de datos

with app.app_context():
    inicio = time.perf_counter()
    db.session.execute(text("SELECT 1"))
    db.session.rollback()          # deja la conexión abierta y sin usar, dentro del pool
    print(f"Consulta inicial: {(time.perf_counter() - inicio) * 1000:.0f} ms\n")

    resultados = []
    for espera in ESPERAS:
        print(f"Esperando {espera} s sin usar la base de datos...", flush=True)
        time.sleep(espera)
        inicio = time.perf_counter()
        db.session.execute(text("SELECT 1"))
        segundos = time.perf_counter() - inicio
        db.session.rollback()
        resultados.append((espera, segundos))
        print(f"   Primera consulta después de {espera} s de espera: {segundos * 1000:.0f} ms\n", flush=True)

lenta = [(e, s) for e, s in resultados if s > 3]
print("=== Resultado ===")
if lenta:
    e, s = lenta[0]
    print(f"✘ Después de {e} s sin usarla, la conexión tardó {s:.1f} s en responder.")
    print("  La conexión se corta cuando está inactiva y la aplicación espera a que se rinda.")
else:
    print("✔ La conexión responde rápido aunque pase un rato sin usarse.")