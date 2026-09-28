from app import db
from sqlalchemy import text


# ======================================================================
# LUGAR
# ======================================================================

def insertar_lugar(nombre, descripcion, direccion, fecha_creacion,
                   fecha_modificacion, administrador_id, estado, contacto):

    resultado = db.session.execute(
        text("""
            INSERT INTO LUGAR
            (
                nombre,
                descripcion,
                direccion,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado,
                contacto
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
                :contacto
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
            'contacto': contacto
        }
    )

    id_lugar = resultado.scalar()

    db.session.commit()

    return id_lugar


def obtener_lugares():

    resultado = db.session.execute(
        text("""
            SELECT
                id_lugar,
                nombre,
                descripcion,
                direccion,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado,
                contacto
            FROM LUGAR
        """)
    )

    lugares = resultado.fetchall()

    return lugares


def obtener_un_lugar(id_lugar):

    resultado = db.session.execute(
        text("""
            SELECT
                id_lugar,
                nombre,
                descripcion,
                direccion,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado,
                contacto
            FROM LUGAR
            WHERE id_lugar = :id_lugar
        """),
        {
            'id_lugar': id_lugar
        }
    )

    lugar = resultado.fetchone()

    return lugar


def actualizar_lugar(
    id_lugar,
    nombre,
    descripcion,
    direccion,
    fecha_modificacion,
    administrador_id,
    estado,
    contacto
):

    db.session.execute(
        text("""
            UPDATE LUGAR
            SET
                nombre = :nombre,
                descripcion = :descripcion,
                direccion = :direccion,
                fecha_modificacion = :fecha_modificacion,
                administrador_id = :administrador_id,
                estado = :estado,
                contacto = :contacto
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
            'id_lugar': id_lugar
        }
    )

    db.session.commit()
