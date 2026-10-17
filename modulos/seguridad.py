"""
Norma 2.1 - Complejidad y rotación de credenciales (manual de políticas, normas y funciones).

  2.1.1  Longitud y complejidad de las claves  -> evaluar_contrasena()
  2.1.2  Renovación programada con avisos       -> dias_para_vencer(), mensaje_de_caducidad(), enviar_correo()
  2.1.3  Claves inéditas (HaveIBeenPwned)       -> veces_filtrada(), revisar_filtracion()

Todos los números de la norma están aquí arriba, en un solo lugar.
Este módulo NO toca la base de datos: solo valida y calcula.
"""
import hashlib
import logging
import math
import os
import re
import smtplib
import unicodedata
import urllib.request
from datetime import datetime, timedelta
from email.message import EmailMessage
from logging.handlers import RotatingFileHandler

# ---------------------------------------------------------------------------
# PARÁMETROS DE LA NORMA (cámbialos aquí si el manual dice otra cosa)
# ---------------------------------------------------------------------------
LONGITUD_MINIMA = 12                 # 2.1.1
LONGITUD_MAXIMA = 128
VIGENCIA_DIAS = 90                   # 2.1.2: cada cuántos días caduca una contraseña
AVISOS_DIAS = (14, 7, 3, 1, 0)       # 2.1.2: días antes de vencer en que se envía el correo (0 = ya venció)
AVISO_EN_PANTALLA_DIAS = 14          # 2.1.2: desde cuántos días antes se avisa dentro de la página
HIBP_TIEMPO_DE_ESPERA = 4            # 2.1.3: segundos máximos que se espera a HaveIBeenPwned

# ---------------------------------------------------------------------------
# 2.1.1  LONGITUD Y COMPLEJIDAD
# ---------------------------------------------------------------------------
_MAYUSCULA = re.compile(r'[A-ZÁÉÍÓÚÑÜ]')
_MINUSCULA = re.compile(r'[a-záéíóúñü]')
_NUMERO = re.compile(r'\d')
_SIMBOLO = re.compile(r'[^A-Za-z0-9ÁÉÍÓÚÑÜáéíóúñü\s]')

# (clave, mensaje de error)
REGLAS = [
    ('longitud', f'La contraseña debe tener al menos {LONGITUD_MINIMA} caracteres.'),
    ('mayuscula', 'Debe incluir al menos una letra mayúscula.'),
    ('minuscula', 'Debe incluir al menos una letra minúscula.'),
    ('numero', 'Debe incluir al menos un número.'),
    ('simbolo', 'Debe incluir al menos un símbolo (por ejemplo ! ? # $ %).'),
]


def _sin_tildes(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()


def datos_personales(correo='', nombre=''):
    """Trozos del correo y del nombre que no deben aparecer dentro de la contraseña (sin importar tildes)."""
    piezas = []
    usuario = _sin_tildes((correo or '').split('@')[0])
    if len(usuario) >= 4:
        piezas.append(usuario)
    for parte in _sin_tildes(nombre or '').split():
        if len(parte) >= 4:
            piezas.append(parte)
    return piezas


def evaluar_contrasena(contrasena, correo='', nombre=''):
    """Devuelve la lista de reglas que NO cumple (vacía = cumple la norma). No consulta internet."""
    cumple = {
        'longitud': len(contrasena) >= LONGITUD_MINIMA,
        'mayuscula': _MAYUSCULA.search(contrasena) is not None,
        'minuscula': _MINUSCULA.search(contrasena) is not None,
        'numero': _NUMERO.search(contrasena) is not None,
        'simbolo': _SIMBOLO.search(contrasena) is not None,
    }
    errores = [mensaje for clave, mensaje in REGLAS if not cumple[clave]]
    if len(contrasena) > LONGITUD_MAXIMA:
        errores.append(f'La contraseña no puede tener más de {LONGITUD_MAXIMA} caracteres.')
    if any(pieza in _sin_tildes(contrasena) for pieza in datos_personales(correo, nombre)):
        errores.append('No puede contener tu nombre ni parte de tu correo.')
    return errores


# ---------------------------------------------------------------------------
# REPORTE DE VALIDACIÓN DE CLAVES (2.1.3): un archivo de registro, SIN contraseñas ni hashes
# ---------------------------------------------------------------------------
_registro = None


def _logger():
    global _registro
    if _registro is None:
        _registro = logging.getLogger('ancestra.validacion_claves')
        _registro.setLevel(logging.INFO)
        _registro.propagate = False
        carpeta = os.getenv('LOG_DIR', 'logs')
        os.makedirs(carpeta, exist_ok=True)
        manejador = RotatingFileHandler(os.path.join(carpeta, 'validacion_claves.log'),
                                        maxBytes=1_000_000, backupCount=5, encoding='utf-8')
        manejador.setFormatter(logging.Formatter('%(asctime)s | %(message)s'))
        _registro.addHandler(manejador)
    return _registro


def registrar_validacion(evento, correo, resultado, detalle=''):
    """Una línea por validación: fecha | evento | correo | resultado | detalle. Nunca la contraseña."""
    try:
        _logger().info(f'{evento} | {correo} | {resultado} | {detalle}')
    except Exception as error:                 # el reporte nunca debe tumbar el registro o el cambio de clave
        print('No se pudo escribir el reporte de validación de claves:', error)


def evaluar_y_registrar(contrasena, correo, nombre, evento):
    """Igual que evaluar_contrasena(), y deja constancia en el reporte si la rechaza."""
    errores = evaluar_contrasena(contrasena, correo, nombre)
    if errores:
        registrar_validacion(evento, correo, 'rechazada_complejidad', f'{len(errores)} regla(s) sin cumplir')
    return errores


# ---------------------------------------------------------------------------
# 2.1.3  CLAVES INÉDITAS: HaveIBeenPwned (Pwned Passwords, método k-anonimato)
#        Solo salen de aquí los primeros 5 caracteres del SHA-1; la contraseña NUNCA se envía.
# ---------------------------------------------------------------------------
def veces_filtrada(contrasena):
    """Cuántas veces aparece la contraseña en filtraciones conocidas. 0 = no aparece. None = no se pudo consultar."""
    sha1 = hashlib.sha1(contrasena.encode('utf-8')).hexdigest().upper()
    prefijo, sufijo = sha1[:5], sha1[5:]
    peticion = urllib.request.Request(
        f'https://api.pwnedpasswords.com/range/{prefijo}',
        headers={'User-Agent': 'Ancestra-validacion-de-claves', 'Add-Padding': 'true'}
    )
    try:
        with urllib.request.urlopen(peticion, timeout=HIBP_TIEMPO_DE_ESPERA) as respuesta:
            texto = respuesta.read().decode('utf-8')
    except Exception as error:
        print('No se pudo consultar HaveIBeenPwned:', error)
        return None
    for linea in texto.splitlines():
        resto, _, veces = linea.partition(':')
        if resto.strip().upper() == sufijo:
            try:
                return int(veces.strip())      # con "Add-Padding" las filas de relleno traen 0
            except ValueError:
                return 0
    return 0


def revisar_filtracion(contrasena, correo, evento):
    """Devuelve un mensaje de error si la contraseña está filtrada; None si se puede usar."""
    veces = veces_filtrada(contrasena)
    if veces:
        registrar_validacion(evento, correo, 'rechazada_filtrada', f'{veces} apariciones')
        numero = f'{veces:,}'.replace(',', '.')           # 1.234 en vez de 1,234
        return (f'Esa contraseña aparece {numero} veces en filtraciones de datos conocidas, '
                'así que no es segura. Elige otra.')
    if veces is None:
        # Si HaveIBeenPwned no responde no se bloquea a nadie, pero queda anotado para revisarlo
        registrar_validacion(evento, correo, 'aceptada_sin_verificar', 'HaveIBeenPwned no respondió')
    else:
        registrar_validacion(evento, correo, 'aceptada', 'no aparece en filtraciones')
    return None


# ---------------------------------------------------------------------------
# 2.1.2  RENOVACIÓN PROGRAMADA
# ---------------------------------------------------------------------------
def vencimiento(ultimo_cambio):
    return ultimo_cambio + timedelta(days=VIGENCIA_DIAS)


def dias_hasta_vencimiento(fecha_de_vencimiento, ahora=None):
    """Días que faltan (se redondea hacia arriba). 0 o menos = ya venció."""
    ahora = ahora or datetime.now()
    return math.ceil((fecha_de_vencimiento - ahora).total_seconds() / 86400)


def dias_para_vencer(ultimo_cambio, ahora=None):
    return dias_hasta_vencimiento(vencimiento(ultimo_cambio), ahora)


def limite_para_avisos(ahora=None):
    """Quien cambió su clave antes de esta fecha ya está dentro de la ventana de avisos (o vencida)."""
    ahora = ahora or datetime.now()
    return ahora - timedelta(days=VIGENCIA_DIAS - max(AVISOS_DIAS))


def mensaje_de_caducidad(nombre, dias):
    if dias <= 0:
        asunto = 'Ancestra: tu contraseña venció'
        cuerpo = (f'Hola {nombre},\n\nTu contraseña de Ancestra venció. La próxima vez que inicies sesión '
                  'tendrás que crear una nueva.\n\nPuedes hacerlo cuando quieras entrando a tu cuenta y eligiendo '
                  '"Cambiar contraseña".\n')
    else:
        plural = 'día' if dias == 1 else 'días'
        asunto = f'Ancestra: tu contraseña vence en {dias} {plural}'
        cuerpo = (f'Hola {nombre},\n\nTu contraseña de Ancestra vence en {dias} {plural}.\n\n'
                  'Para cambiarla, inicia sesión y elige "Cambiar contraseña" en el menú de tu cuenta.\n')
    return asunto, cuerpo + '\nSi ya la cambiaste, ignora este mensaje.\n'


def enviar_correo(destino, asunto, cuerpo):
    """Envía un correo con los datos MAIL_* del archivo .env. Devuelve False si no hay correo configurado o falla."""
    host = os.getenv('MAIL_HOST')
    if not host:
        return False
    puerto = int(os.getenv('MAIL_PORT', '587'))
    usuario = os.getenv('MAIL_USER')
    clave = os.getenv('MAIL_PASSWORD')
    mensaje = EmailMessage()
    mensaje['Subject'] = asunto
    mensaje['From'] = os.getenv('MAIL_FROM', usuario or 'no-responder@ancestra.local')
    mensaje['To'] = destino
    mensaje.set_content(cuerpo)
    try:
        if puerto == 465:
            with smtplib.SMTP_SSL(host, puerto, timeout=15) as servidor:
                if usuario:
                    servidor.login(usuario, clave)
                servidor.send_message(mensaje)
        else:
            with smtplib.SMTP(host, puerto, timeout=15) as servidor:
                servidor.starttls()
                if usuario:
                    servidor.login(usuario, clave)
                servidor.send_message(mensaje)
        return True
    except Exception as error:
        print('No se pudo enviar el correo:', error)
        return False