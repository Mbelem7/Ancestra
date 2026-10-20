from app import db
from sqlalchemy import text


def insertar_estudiante(persona_id, estado):

    resultado = db.session.execute(
        text("""
            INSERT INTO estudiante
            (
                persona_id,
                estado
            )
            VALUES
            (
                :persona_id,
                :estado
            )
            RETURNING id_estudiante
        """),
        {
            'persona_id': persona_id,
            'estado': estado
        }
    )

    id_estudiante = resultado.scalar()

    db.session.commit()

    return id_estudiante


def obtener_estudiantes():

    resultado = db.session.execute(
        text("""
            SELECT
                e.id_estudiante,
                e.estado,
                p.id_persona,
                p.nombre_1,
                p.nombre_2,
                p.apellido_1,
                p.apellido_2,
                p.fecha_nacimiento,
                p.correo
            FROM estudiante e
            INNER JOIN persona p ON p.id_persona = e.persona_id
        """)
    )

    estudiantes = resultado.fetchall()

    return estudiantes


def obtener_un_estudiante(id_estudiante):

    resultado = db.session.execute(
        text("""
            SELECT
                e.id_estudiante,
                e.estado,
                p.id_persona,
                p.nombre_1,
                p.nombre_2,
                p.apellido_1,
                p.apellido_2,
                p.fecha_nacimiento,
                p.correo
            FROM estudiante e
            INNER JOIN persona p ON p.id_persona = e.persona_id
            WHERE e.id_estudiante = :id_estudiante
        """),
        {
            'id_estudiante': id_estudiante
        }
    )

    estudiante = resultado.fetchone()

    return estudiante


def obtener_estudiante_por_persona(persona_id):
    # Para saber qué estudiante es la persona que inició sesión

    resultado = db.session.execute(
        text("""
            SELECT
                id_estudiante,
                estado,
                persona_id
            FROM estudiante
            WHERE persona_id = :persona_id
        """),
        {
            'persona_id': persona_id
        }
    )

    estudiante = resultado.fetchone()

    return estudiante


def actualizar_estado_estudiante(id_estudiante, estado):

    db.session.execute(
        text("""
            UPDATE estudiante
            SET
                estado = :estado
            WHERE id_estudiante = :id_estudiante
        """),
        {
            'estado': estado,
            'id_estudiante': id_estudiante
        }
    )

    db.session.commit()

def contar_estudiantes_activos():
    # Cuántos estudiantes tienen su registro y su cuenta activos

    resultado = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM estudiante e
            INNER JOIN persona p ON p.id_persona = e.persona_id
            WHERE e.estado = 'activo'
              AND p.estado = 'activo'
        """)
    )

    return resultado.scalar() or 0