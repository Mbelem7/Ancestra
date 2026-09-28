from app import db
from sqlalchemy import text


def insertar_estudiante(persona_id):

    resultado = db.session.execute(
        text("""
            INSERT INTO ESTUDIANTE
            (
                persona_id
            )
            VALUES
            (
                :persona_id
            )
            RETURNING id_estudiante
        """),
        {
            'persona_id': persona_id
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
                p.id_persona,
                p.nombre1,
                p.nombre2,
                p.apellido1,
                p.apellido2,
                p.fecha_nacimiento,
                p.correo,
                p.estado
            FROM ESTUDIANTE e
            INNER JOIN PERSONA p ON p.id_persona = e.persona_id
        """)
    )

    estudiantes = resultado.fetchall()

    return estudiantes


def obtener_un_estudiante(id_estudiante):

    resultado = db.session.execute(
        text("""
            SELECT
                e.id_estudiante,
                p.id_persona,
                p.nombre1,
                p.nombre2,
                p.apellido1,
                p.apellido2,
                p.fecha_nacimiento,
                p.correo,
                p.estado
            FROM ESTUDIANTE e
            INNER JOIN PERSONA p ON p.id_persona = e.persona_id
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
                persona_id
            FROM ESTUDIANTE
            WHERE persona_id = :persona_id
        """),
        {
            'persona_id': persona_id
        }
    )

    estudiante = resultado.fetchone()

    return estudiante