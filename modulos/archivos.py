from app import db
from sqlalchemy import text, bindparam


#AGREGA UN NUEVO ARCHIVO
def insertar_archivo(nombre, descripcion, url, categoria, tipo,
                     fecha_creacion, fecha_modificacion,
                     administrador_id, estado):

    resultado = db.session.execute(
        text("""
            INSERT INTO archivo
            (
                nombre,
                descripcion,
                url,
                categoria_id,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            )
            VALUES
            (
                :nombre,
                :descripcion,
                :url,
                :categoria,
                :tipo,
                :fecha_creacion,
                :fecha_modificacion,
                :administrador_id,
                :estado
            )
            RETURNING id_archivo
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'url': url,
            'categoria': categoria,
            'tipo': tipo,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'administrador_id': administrador_id,
            'estado': estado
        }
    )

    id_archivo = resultado.scalar()

    db.session.commit()

    return id_archivo


#CONSULTA PARA MOSTRAR EL ARCHIVO
def obtener_archivos():

    resultado = db.session.execute(
        text("""
            SELECT
                id_archivo,
                nombre,
                descripcion,
                url,
                categoria_id,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            FROM archivo
        """)
    )

    archivos = resultado.fetchall()

    return archivos

#CONSULTA PARA OBTENER 1 SOLO ARCHIVO SEGUN SI ID
def obtener_un_archivo(id_archivo):

    resultado = db.session.execute(
        text("""
            SELECT
                id_archivo,
                nombre,
                descripcion,
                url,
                categoria_id,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            FROM archivo
            WHERE id_archivo = :id_archivo
        """),
        {
            'id_archivo': id_archivo
        }
    )

    archivo = resultado.fetchone()

    return archivo

#OBTIENE EL ARCHIVO POR TIPO
def obtener_archivos_por_tipo(tipo):
    # Base de las funciones de mostrar por tipo (libros, documentos, etc.)
    resultado = db.session.execute(
        text("""
            SELECT
                id_archivo,
                nombre,
                descripcion,
                url,
                categoria_id,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            FROM archivo
            WHERE tipo = :tipo
        """),
        {
            'tipo': tipo
        }
    )

    archivos = resultado.fetchall()

    return archivos

#OBTIENE LOS ARCHIVOS POR SU CATEGORIA: HISTORIA, GEOGRAFIA, MITOS, ETC
def obtener_archivos_por_categoria(categoria_id):

    resultado = db.session.execute(
        text("""
            SELECT
                id_archivo,
                nombre,
                descripcion,
                url,
                categoria_id,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            FROM archivo
            WHERE categoria_id = :categoria_id
        """),
        {
            'categoria_id': categoria_id
        }
    )

    archivos = resultado.fetchall()

    return archivos

#SE OBTIENEN ARCHIVOS POR SU NOMBRE (PARA UNA BUSQUEDA)
def obtener_archivos_por_nombre(nombre):
    # Para la búsqueda (barra de búsqueda de biblioteca/galería)
    resultado = db.session.execute(
        text("""
            SELECT
                id_archivo,
                nombre,
                descripcion,
                url,
                categoria_id,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            FROM archivo
            WHERE nombre ILIKE :nombre
        """),
        {
            'nombre': f"%{nombre}%"
        }
    )

    archivos = resultado.fetchall()

    return archivos

#ACTUALIZAR UN ARCHIVO
def actualizar_archivo(
    id_archivo,
    nombre,
    descripcion,
    url,
    categoria_id,
    tipo,
    fecha_modificacion,
    administrador_id,
    estado
):

    db.session.execute(
        text("""
            UPDATE archivo
            SET
                nombre = :nombre,
                descripcion = :descripcion,
                url = :url,
                categoria_id = :categoria_id,
                tipo = :tipo,
                fecha_modificacion = :fecha_modificacion,
                administrador_id = :administrador_id,
                estado = :estado
            WHERE id_archivo = :id_archivo
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'url': url,
            'categoria_id': categoria_id,
            'tipo': tipo,
            'fecha_modificacion': fecha_modificacion,
            'administrador_id': administrador_id,
            'estado': estado,
            'id_archivo': id_archivo
        }
    )

    db.session.commit()


# ======================================================================
# Para mostrar en la BIBLIOTECA
# ======================================================================

def obtener_libros():
    return obtener_archivos_por_tipo('libro')


def obtener_documentos():
    return obtener_archivos_por_tipo('documento')


def obtener_cuentos():
    return obtener_archivos_por_tipo('cuento')


def obtener_archivos_por_tipos(tipos):
    # tipos: lista de strings, ej. ['libro', 'documento', 'cuento', 'ensayo']
    resultado = db.session.execute(
        text("""
            SELECT
                id_archivo,
                nombre,
                descripcion,
                url,
                categoria_id,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            FROM archivo
            WHERE tipo IN :tipos
        """).bindparams(bindparam('tipos', expanding=True)),
        {
            'tipos': tipos
        }
    )

    archivos = resultado.fetchall()

    return archivos


def obtener_archivos_biblioteca():
    # Todo lo que se muestra en la biblioteca (no imágenes ni videos)
    return obtener_archivos_por_tipos(['libro', 'documento', 'cuento', 'tesis', 'ensayo'])


# ======================================================================
# Para mostrar en la GALERÍA
# ======================================================================

def obtener_imagenes():
    return obtener_archivos_por_tipo('imagen')


def obtener_videos():
    return obtener_archivos_por_tipo('video')

def obtener_archivos_galeria():
    # Todo lo que se muestra en la galería (imágenes y videos juntos)

    return obtener_archivos_por_tipos(['imagen', 'video'])