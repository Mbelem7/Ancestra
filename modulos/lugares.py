from app import db
from sqlalchemy import text


# Columnas de un lugar. Las de la ficha ampliada (reseña, horario y ubicación) van AL FINAL,
# para que las posiciones que ya usan las pantallas (l[0] ... l[10]) no cambien.
# lugar: (id_lugar, nombre, descripcion, direccion, fecha_creacion, fecha_modificacion, administrador_id,
#         estado, contacto, latitud, longitud,
#         resena, horario, municipio_id, municipio, departamento, id_departamento)
_COLUMNAS = """
                l.id_lugar,
                l.nombre,
                l.descripcion,
                l.direccion,
                l.fecha_creacion,
                l.fecha_modificacion,
                l.administrador_id,
                l.estado,
                l.contacto,
                l.latitud,
                l.longitud,
                l.resena,
                l.horario,
                l.municipio_id,
                mu.nombre,
                de.nombre,
                de.id_departamento
"""

_DESDE = """
            FROM lugar l
            LEFT JOIN municipio mu ON mu.id_municipio = l.municipio_id
            LEFT JOIN departamento de ON de.id_departamento = mu.departamento_id
"""


def insertar_lugar(nombre, descripcion, direccion, fecha_creacion,
                   fecha_modificacion, administrador_id, estado, contacto,
                   latitud, longitud, resena=None, horario=None, municipio_id=None):

    resultado = db.session.execute(
        text("""
            INSERT INTO lugar
            (
                nombre,
                descripcion,
                direccion,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado,
                contacto,
                latitud,
                longitud,
                resena,
                horario,
                municipio_id
            )
            VALUES
            (
                :nombre,
                :descripcion,
                :direccion,
                :fecha_creacion,
                :fecha_modificacion,
                :administrador_id,
                :estado,
                :contacto,
                :latitud,
                :longitud,
                :resena,
                :horario,
                :municipio_id
            )
            RETURNING id_lugar
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'direccion': direccion,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'administrador_id': administrador_id,
            'estado': estado,
            'contacto': contacto,
            'latitud': latitud,
            'longitud': longitud,
            'resena': resena,
            'horario': horario,
            'municipio_id': municipio_id
        }
    )

    id_lugar = resultado.scalar()

    db.session.commit()

    return id_lugar


def obtener_lugares(solo_activos=True):
    # solo_activos: si es True, no trae los lugares inactivos (quedan como dato histórico)
    filtro_estado = "WHERE l.estado = 'activo'" if solo_activos else ""

    resultado = db.session.execute(
        text(f"""
            SELECT {_COLUMNAS}
            {_DESDE}
            {filtro_estado}
        """)
    )

    return resultado.fetchall()


def obtener_un_lugar(id_lugar):
    # Sin filtro de estado: la usan la pantalla de editar y la ficha (el administrador puede abrir un inactivo)

    resultado = db.session.execute(
        text(f"""
            SELECT {_COLUMNAS}
            {_DESDE}
            WHERE l.id_lugar = :id_lugar
        """),
        {
            'id_lugar': id_lugar
        }
    )

    return resultado.fetchone()


def obtener_lugares_por_nombre(nombre, solo_activos=True):
    # Para la búsqueda (barra de búsqueda del mapa)
    filtro_estado = "AND l.estado = 'activo'" if solo_activos else ""

    resultado = db.session.execute(
        text(f"""
            SELECT {_COLUMNAS}
            {_DESDE}
            WHERE l.nombre ILIKE :nombre
            {filtro_estado}
        """),
        {
            'nombre': f"%{nombre}%"
        }
    )

    return resultado.fetchall()


def actualizar_lugar(
    id_lugar,
    nombre,
    descripcion,
    direccion,
    fecha_modificacion,
    administrador_id,
    estado,
    contacto,
    latitud,
    longitud,
    resena=None,
    horario=None,
    municipio_id=None
):

    db.session.execute(
        text("""
            UPDATE lugar
            SET
                nombre = :nombre,
                descripcion = :descripcion,
                direccion = :direccion,
                fecha_modificacion = :fecha_modificacion,
                administrador_id = :administrador_id,
                estado = :estado,
                contacto = :contacto,
                latitud = :latitud,
                longitud = :longitud,
                resena = :resena,
                horario = :horario,
                municipio_id = :municipio_id
            WHERE id_lugar = :id_lugar
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'direccion': direccion,
            'fecha_modificacion': fecha_modificacion,
            'administrador_id': administrador_id,
            'estado': estado,
            'contacto': contacto,
            'latitud': latitud,
            'longitud': longitud,
            'resena': resena,
            'horario': horario,
            'municipio_id': municipio_id,
            'id_lugar': id_lugar
        }
    )

    db.session.commit()


# ======================================================================
# Fotos del lugar (tabla lugar_archivo): se eligen de la galería
# ======================================================================

def obtener_fotos_de_lugar(lugar_id, solo_activos=True):
    # Devuelve: (id_archivo, nombre, url, tipo)
    filtro_estado = "AND a.estado = 'activo'" if solo_activos else ""

    resultado = db.session.execute(
        text(f"""
            SELECT
                a.id_archivo,
                a.nombre,
                a.url,
                a.tipo
            FROM lugar_archivo la
            INNER JOIN archivo a ON a.id_archivo = la.archivo_id
            WHERE la.lugar_id = :lugar_id
            {filtro_estado}
            ORDER BY la.id_lugar_archivo
        """),
        {
            'lugar_id': lugar_id
        }
    )

    return resultado.fetchall()


def guardar_fotos_de_lugar(lugar_id, ids_archivos):
    # Reemplaza las fotos del lugar por las elegidas en el formulario (solo se borran las relaciones;
    # las imágenes siguen en la galería)

    db.session.execute(
        text("DELETE FROM lugar_archivo WHERE lugar_id = :lugar_id"),
        {'lugar_id': lugar_id}
    )
    for archivo_id in ids_archivos:
        db.session.execute(
            text("""
                INSERT INTO lugar_archivo (lugar_id, archivo_id)
                VALUES (:lugar_id, :archivo_id)
            """),
            {'lugar_id': lugar_id, 'archivo_id': archivo_id}
        )

    db.session.commit()


# ======================================================================
# Fuentes de la información del lugar (tabla lugar_autor), con la misma tabla de autores
# ======================================================================

def obtener_autores_de_lugar(lugar_id):
    # Devuelve: (id_autor, nombre, tipo, origen, descripcion), igual que obtener_autores_por_archivo

    resultado = db.session.execute(
        text("""
            SELECT
                a.id_autor,
                a.nombre,
                a.tipo,
                a.origen,
                a.descripcion
            FROM lugar_autor la
            INNER JOIN autor a ON a.id_autor = la.autor_id
            WHERE la.lugar_id = :lugar_id
            ORDER BY la.id_lugar_autor
        """),
        {
            'lugar_id': lugar_id
        }
    )

    return resultado.fetchall()


def insertar_lugar_autor(lugar_id, autor_id):

    db.session.execute(
        text("""
            INSERT INTO lugar_autor (lugar_id, autor_id)
            VALUES (:lugar_id, :autor_id)
        """),
        {
            'lugar_id': lugar_id,
            'autor_id': autor_id
        }
    )

    db.session.commit()


def eliminar_autores_de_lugar(lugar_id):
    # Al editar se quitan las relaciones y se vuelven a guardar las del formulario (los autores siguen registrados)

    db.session.execute(
        text("DELETE FROM lugar_autor WHERE lugar_id = :lugar_id"),
        {'lugar_id': lugar_id}
    )

    db.session.commit()