from app import db
from sqlalchemy import text


def insertar_juego(nombre, descripcion, tipo, fecha_creacion,
                   fecha_modificacion, administrador_id, estado):

    resultado = db.session.execute(
        text("""
            INSERT INTO JUEGO
            (
                nombre,
                descripcion,
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
                :tipo,
                :fecha_creacion,
                :fecha_modificacion,
                :administrador_id,
                :estado
            )
            RETURNING id_juego
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'tipo': tipo,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'administrador_id': administrador_id,
            'estado': estado
        }
    )

    id_juego = resultado.scalar()

    db.session.commit()

    return id_juego


def obtener_juegos():

    resultado = db.session.execute(
        text("""
            SELECT
                id_juego,
                nombre,
                descripcion,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            FROM JUEGO
        """)
    )

    juegos = resultado.fetchall()

    return juegos


def obtener_juegos_predeterminados():
    # Juegos que NO vienen de una plantilla de docente

    resultado = db.session.execute(
        text("""
            SELECT
                j.id_juego,
                j.nombre,
                j.descripcion,
                j.tipo,
                j.fecha_creacion,
                j.fecha_modificacion,
                j.administrador_id,
                j.estado
            FROM JUEGO j
            LEFT JOIN PLANTILLA p ON p.juego_id = j.id_juego
            WHERE p.id_plantilla IS NULL
        """)
    )

    juegos = resultado.fetchall()

    return juegos


def obtener_un_juego(id_juego):

    resultado = db.session.execute(
        text("""
            SELECT
                id_juego,
                nombre,
                descripcion,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            FROM JUEGO
            WHERE id_juego = :id_juego
        """),
        {
            'id_juego': id_juego
        }
    )

    juego = resultado.fetchone()

    return juego


def actualizar_juego(
    id_juego,
    nombre,
    descripcion,
    tipo,
    fecha_modificacion,
    administrador_id,
    estado
):

    db.session.execute(
        text("""
            UPDATE JUEGO
            SET
                nombre = :nombre,
                descripcion = :descripcion,
                tipo = :tipo,
                fecha_modificacion = :fecha_modificacion,
                administrador_id = :administrador_id,
                estado = :estado
            WHERE id_juego = :id_juego
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'tipo': tipo,
            'fecha_modificacion': fecha_modificacion,
            'administrador_id': administrador_id,
            'estado': estado,
            'id_juego': id_juego
        }
    )

    db.session.commit()