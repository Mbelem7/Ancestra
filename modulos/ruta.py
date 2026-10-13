from app import db
from sqlalchemy import text

def insertar_ruta(nombre, descripcion, latitud, longitud, fecha_creacion,
                  fecha_modificacion, lugar_id, administrador_id, estado):

    db.session.execute(
        text("""
            INSERT INTO ruta
            (
                nombre,
                descripcion,
                latitud,
                longitud,
                fecha_creacion,
                fecha_modificacion,
                lugar_id,
                administrador_id,
                estado
            )
            VALUES
            (
                :nombre,
                :descripcion,
                :latitud,
                :longitud,
                :fecha_creacion,
                :fecha_modificacion,
                :lugar_id,
                :administrador_id,
                :estado
            )
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'latitud': latitud,
            'longitud': longitud,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'lugar_id': lugar_id,
            'administrador_id': administrador_id,
            'estado': estado
        }
    )

    db.session.commit()


def obtener_rutas():

    resultado = db.session.execute(
        text("""
            SELECT
                id_ruta,
                nombre,
                descripcion,
                latitud,
                longitud,
                fecha_creacion,
                fecha_modificacion,
                lugar_id,
                administrador_id,
                estado
            FROM ruta
        """)
    )

    rutas = resultado.fetchall()

    return rutas


def obtener_rutas_por_lugar(lugar_id):

    resultado = db.session.execute(
        text("""
            SELECT
                id_ruta,
                nombre,
                descripcion,
                latitud,
                longitud,
                fecha_creacion,
                fecha_modificacion,
                lugar_id,
                administrador_id,
                estado
            FROM ruta
            WHERE lugar_id = :lugar_id
        """),
        {
            'lugar_id': lugar_id
        }
    )

    rutas = resultado.fetchall()

    return rutas


def obtener_una_ruta(id_ruta):

    resultado = db.session.execute(
        text("""
            SELECT
                id_ruta,
                nombre,
                descripcion,
                latitud,
                longitud,
                fecha_creacion,
                fecha_modificacion,
                lugar_id,
                administrador_id,
                estado
            FROM ruta
            WHERE id_ruta = :id_ruta
        """),
        {
            'id_ruta': id_ruta
        }
    )

    ruta = resultado.fetchone()

    return ruta


def actualizar_ruta(
    id_ruta,
    nombre,
    descripcion,
    latitud,
    longitud,
    fecha_modificacion,
    lugar_id,
    administrador_id,
    estado
):

    db.session.execute(
        text("""
            UPDATE ruta
            SET
                nombre = :nombre,
                descripcion = :descripcion,
                latitud = :latitud,
                longitud = :longitud,
                fecha_modificacion = :fecha_modificacion,
                lugar_id = :lugar_id,
                administrador_id = :administrador_id,
                estado = :estado
            WHERE id_ruta = :id_ruta
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'latitud': latitud,
            'longitud': longitud,
            'fecha_modificacion': fecha_modificacion,
            'lugar_id': lugar_id,
            'administrador_id': administrador_id,
            'estado': estado,
            'id_ruta': id_ruta
        }
    )

    db.session.commit()