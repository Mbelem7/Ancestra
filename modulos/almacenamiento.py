# ======================================================================
# Dónde se guardan los archivos que se suben a Ancestra (PDF, imágenes, videos y fotos de lugares)
#
# Si en el .env están SUPABASE_URL, SUPABASE_SERVICE_KEY y SUPABASE_BUCKET, se guardan en Supabase Storage
# (fuera del servidor: no se pierden cuando Render reinicia). Si no están, se guardan como antes, en static/assets.
# En la base de datos solo queda el enlace (o la ruta) del archivo, nunca el archivo.
# ======================================================================
import os
import mimetypes
import urllib.request
import urllib.error
import urllib.parse

import pymupdf


# Carpeta del bucket → carpeta local equivalente (la que se usa si Storage no está configurado)
CARPETAS_LOCALES = {
    'docs': 'static/assets/docs',
    'docs/portadas': 'static/assets/docs/portadas',
    'img': 'static/assets/img',
    'lugares': 'static/assets/img/lugares',
}


def _config():
    return (os.getenv('SUPABASE_URL', '').strip().rstrip('/'),
            os.getenv('SUPABASE_SERVICE_KEY', '').strip(),
            os.getenv('SUPABASE_BUCKET', 'ancestra').strip())


def storage_activo():
    url, clave, bucket = _config()
    return bool(url and clave and bucket)


def es_remota(ruta):
    # True si la ruta guardada es un enlace de internet (Storage) y no una ruta de static
    return str(ruta or '').startswith(('http://', 'https://'))


def url_publica(ruta_en_bucket):
    url, _, bucket = _config()
    return f"{url}/storage/v1/object/public/{bucket}/{urllib.parse.quote(ruta_en_bucket)}"


def _subir_a_storage(datos, ruta_en_bucket, tipo_mime):
    url, clave, bucket = _config()
    peticion = urllib.request.Request(
        f"{url}/storage/v1/object/{bucket}/{urllib.parse.quote(ruta_en_bucket)}",
        data=datos,
        method='POST',
        headers={
            'Authorization': f'Bearer {clave}',
            'apikey': clave,
            'Content-Type': tipo_mime,
            'x-upsert': 'true',          # si ya existe un archivo con ese nombre, lo reemplaza
            'cache-control': '3600',
        },
    )
    try:
        with urllib.request.urlopen(peticion, timeout=180) as respuesta:
            respuesta.read()
    except urllib.error.HTTPError as error:
        detalle = error.read().decode('utf-8', 'replace')[:300]
        raise RuntimeError(f"Supabase Storage respondió {error.code}: {detalle}") from error
    return url_publica(ruta_en_bucket)


def guardar(datos, carpeta, nombre, tipo_mime=None):
    """Guarda los bytes de un archivo. carpeta: 'docs', 'docs/portadas', 'img' o 'lugares'.
    Devuelve lo que se guarda en la base de datos: el enlace de Storage o la ruta local (static/assets/...)."""
    tipo_mime = tipo_mime or mimetypes.guess_type(nombre)[0] or 'application/octet-stream'
    if storage_activo():
        return _subir_a_storage(datos, f"{carpeta}/{nombre}", tipo_mime)

    carpeta_local = CARPETAS_LOCALES[carpeta]
    os.makedirs(carpeta_local, exist_ok=True)
    with open(os.path.join(carpeta_local, nombre), 'wb') as destino:
        destino.write(datos)
    return f"{carpeta_local}/{nombre}"


def portada_de_pdf(datos):
    """La primera página de un PDF como imagen JPG (en bytes), de 400 px de ancho. None si el PDF no se puede leer."""
    try:
        with pymupdf.open(stream=datos, filetype='pdf') as pdf:
            pagina = pdf[0]
            zoom = 400 / pagina.rect.width
            imagen = pagina.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            try:
                return imagen.tobytes('jpeg', jpg_quality=80)
            except TypeError:                   # versiones de PyMuPDF sin el ajuste de calidad
                return imagen.tobytes('jpeg')
    except Exception as error:
        print('No se pudo generar la portada del PDF:', error)
        return None