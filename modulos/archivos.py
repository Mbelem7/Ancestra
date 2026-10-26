from app import db
from sqlalchemy import text, bindparam


# Regla de Ancestra: un archivo en estado inactivo es un dato histórico. Sigue en la base de datos,
# pero no se muestra en la plataforma. Las consultas para mostrar reciben solo_activos=True por defecto;
# el administrador puede pedir solo_activos=False para ver también los inactivos (y poder reactivarlos).
def _filtro_estado(solo_activos):
    # Texto fijo escrito aquí (nunca algo que escriba el usuario), por eso es seguro insertarlo en el SQL
    return "AND estado = 'activo'" if solo_activos else ""


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


#CONSULTA PARA MOSTRAR EL ARCHIVO (todos, activos e inactivos: es la lista completa de la tabla)
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
# (sin filtro de estado: la usa la pantalla de editar, que debe poder abrir un inactivo para reactivarlo)
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
def obtener_archivos_por_tipo(tipo, solo_activos=True):
    # Base de las funciones de mostrar por tipo (libros, documentos, etc.)
    resultado = db.session.execute(
        text(f"""
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
            {_filtro_estado(solo_activos)}
        """),
        {
            'tipo': tipo
        }
    )

    archivos = resultado.fetchall()

    return archivos

#OBTIENE LOS ARCHIVOS POR SU CATEGORIA: HISTORIA, GEOGRAFIA, MITOS, ETC
def obtener_archivos_por_categoria(categoria_id, solo_activos=True):

    resultado = db.session.execute(
        text(f"""
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
            {_filtro_estado(solo_activos)}
        """),
        {
            'categoria_id': categoria_id
        }
    )

    archivos = resultado.fetchall()

    return archivos

#SE OBTIENEN ARCHIVOS POR SU NOMBRE (PARA UNA BUSQUEDA)
def obtener_archivos_por_nombre(nombre, solo_activos=True):
    # Para la búsqueda (barra de búsqueda de biblioteca/galería)
    resultado = db.session.execute(
        text(f"""
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
            {_filtro_estado(solo_activos)}
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

def obtener_libros(solo_activos=True):
    return obtener_archivos_por_tipo('libro', solo_activos)


def obtener_documentos(solo_activos=True):
    return obtener_archivos_por_tipo('documento', solo_activos)


def obtener_cuentos(solo_activos=True):
    return obtener_archivos_por_tipo('cuento', solo_activos)

def obtener_diccionario(solo_activos=True):
    return obtener_archivos_por_tipo('diccionario', solo_activos)


def obtener_archivos_por_tipos(tipos, solo_activos=True):
    # tipos: lista de strings, ej. ['libro', 'documento', 'cuento', 'ensayo']
    resultado = db.session.execute(
        text(f"""
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
            {_filtro_estado(solo_activos)}
        """).bindparams(bindparam('tipos', expanding=True)),
        {
            'tipos': tipos
        }
    )

    archivos = resultado.fetchall()

    return archivos


def obtener_archivos_excepto_tipos(tipos, solo_activos=True):
    # Todos los archivos cuyo tipo NO está en la lista (ej. ['imagen', 'video'])
    resultado = db.session.execute(
        text(f"""
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
            WHERE tipo NOT IN :tipos
            {_filtro_estado(solo_activos)}
        """).bindparams(bindparam('tipos', expanding=True)),
        {
            'tipos': tipos
        }
    )

    archivos = resultado.fetchall()

    return archivos


def obtener_archivos_biblioteca(solo_activos=True):
    # Todo lo que se muestra en la biblioteca: todo lo que NO es imagen ni video
    # (así un tipo de documento nuevo aparece solo, sin tocar esta consulta)
    return obtener_archivos_excepto_tipos(['imagen', 'video'], solo_activos)

# ======================================================================
# Para mostrar en la GALERÍA
# ======================================================================

def obtener_imagenes(solo_activos=True):
    return obtener_archivos_por_tipo('imagen', solo_activos)


def obtener_videos(solo_activos=True):
    return obtener_archivos_por_tipo('video', solo_activos)

def obtener_archivos_galeria(solo_activos=True):
    # Todo lo que se muestra en la galería (imágenes y videos juntos)
    return obtener_archivos_por_tipos(['imagen', 'video'], solo_activos)