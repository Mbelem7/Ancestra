from app import db
from sqlalchemy import text


def insertar_pregunta(enunciado, fecha_creacion, fecha_modificacion,
                      plantilla_id, juego_id):

    resultado = db.session.execute(
        text("""
            INSERT INTO PREGUNTA
            (
                enunciado,
                fecha_creacion,
                fecha_modificacion,
                plantilla_id,
                juego_id
            )
            VALUES
            (
                :enunciado,
                :fecha_creacion,
                :fecha_modificacion,
                :plantilla_id,
                :juego_id
            )
            RETURNING id_pregunta
        """),
        {
            'enunciado': enunciado,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'plantilla_id': plantilla_id,
            'juego_id': juego_id
        }
    )

    id_pregunta = resultado.scalar()

    db.session.commit()

    return id_pregunta


def obtener_preguntas():

    resultado = db.session.execute(
        text("""
            SELECT
                id_pregunta,
                enunciado,
                fecha_creacion,
                fecha_modificacion,
                plantilla_id,
                juego_id
            FROM PREGUNTA
        """)
    )

    preguntas = resultado.fetchall()

    return preguntas


def obtener_preguntas_por_juego(juego_id):

    resultado = db.session.execute(
        text("""
            SELECT
                id_pregunta,
                enunciado,
                fecha_creacion,
                fecha_modificacion,
                plantilla_id,
                juego_id
            FROM PREGUNTA
            WHERE juego_id = :juego_id
        """),
        {
            'juego_id': juego_id
        }
    )

    preguntas = resultado.fetchall()

    return preguntas


def obtener_preguntas_por_plantilla(plantilla_id):

    resultado = db.session.execute(
        text("""
            SELECT
                id_pregunta,
                enunciado,
                fecha_creacion,
                fecha_modificacion,
                plantilla_id,
                juego_id
            FROM PREGUNTA
            WHERE plantilla_id = :plantilla_id
        """),
        {
            'plantilla_id': plantilla_id
        }
    )

    preguntas = resultado.fetchall()

    return preguntas


def obtener_una_pregunta(id_pregunta):

    resultado = db.session.execute(
        text("""
            SELECT
                id_pregunta,
                enunciado,
                fecha_creacion,
                fecha_modificacion,
                plantilla_id,
                juego_id
            FROM PREGUNTA
            WHERE id_pregunta = :id_pregunta
        """),
        {
            'id_pregunta': id_pregunta
        }
    )

    pregunta = resultado.fetchone()

    return pregunta


def actualizar_pregunta(
    id_pregunta,
    enunciado,
    fecha_modificacion,
    plantilla_id,
    juego_id
):

    db.session.execute(
        text("""
            UPDATE PREGUNTA
            SET
                enunciado = :enunciado,
                fecha_modificacion = :fecha_modificacion,
                plantilla_id = :plantilla_id,
                juego_id = :juego_id
            WHERE id_pregunta = :id_pregunta
        """),
        {
            'enunciado': enunciado,
            'fecha_modificacion': fecha_modificacion,
            'plantilla_id': plantilla_id,
            'juego_id': juego_id,
            'id_pregunta': id_pregunta
        }
    )

    db.session.commit()