from app import db
from sqlalchemy import text


def insertar_administrador(persona_id, nombre_usuario):

    resultado = db.session.execute(
        text("""
            INSERT INTO administrador
            (
                persona_id,
                nombre_usuario
            )
            VALUES
            (
                :persona_id,
                :nombre_usuario
            )
            RETURNING id_administrador
        """),
        {
            'persona_id': persona_id,
            'nombre_usuario': nombre_usuario
        }
    )

    id_administrador = resultado.scalar()

    db.session.commit()

    return id_administrador


def obtener_administrador_por_persona(persona_id):
    # Para saber qué administrador es la persona que inició sesión

    resultado = db.session.execute(
        text("""
            SELECT
                id_administrador,
                nombre_usuario,
                persona_id
            FROM administrador
            WHERE persona_id = :persona_id
        """),
        {
            'persona_id': persona_id
        }
    )

    administrador = resultado.fetchone()

    return administrador