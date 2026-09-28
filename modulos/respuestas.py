from app import db
from sqlalchemy import text


def insertar_respuesta(respuesta, tipo, fecha_creacion,
                       fecha_modificacion, pregunta_id, juego_id):
    # tipo: aquí puedes guardar, por ejemplo, 'correcta' / 'incorrecta'

    db.session.execute(
        text("""
            INSERT INTO RESPUESTA
            (
                respuesta,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                pregunta_id,
                juego_id
            )
            VALUES
            (
                :respuesta,
                :tipo,
                :fecha_creacion,
                :fecha_modificacion,
                :pregunta_id,
                :juego_id
            )
        """),
        {
            'respuesta': respuesta,
            'tipo': tipo,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'pregunta_id': pregunta_id,
            'juego_id': juego_id
        }
    )

    db.session.commit()


def obtener_respuestas():

    resultado = db.session.execute(
        text("""
            SELECT
                id_respuesta,
                respuesta,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                pregunta_id,
                juego_id
            FROM RESPUESTA
        """)
    )

    respuestas = resultado.fetchall()

    return respuestas


def obtener_respuestas_por_pregunta(pregunta_id):

    resultado = db.session.execute(
        text("""
            SELECT
                id_respuesta,
                respuesta,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                pregunta_id,
                juego_id
            FROM RESPUESTA
            WHERE pregunta_id = :pregunta_id
        """),
        {
            'pregunta_id': pregunta_id
        }
    )

    respuestas = resultado.fetchall()

    return respuestas


def obtener_una_respuesta(id_respuesta):

    resultado = db.session.execute(
        text("""
            SELECT
                id_respuesta,
                respuesta,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                pregunta_id,
                juego_id
            FROM RESPUESTA
            WHERE id_respuesta = :id_respuesta
        """),
        {
            'id_respuesta': id_respuesta
        }
    )

    respuesta = resultado.fetchone()

    return respuesta


def actualizar_respuesta(
    id_respuesta,
    respuesta,
    tipo,
    fecha_modificacion,
    pregunta_id,
    juego_id
):

    db.session.execute(
        text("""
            UPDATE RESPUESTA
            SET
                respuesta = :respuesta,
                tipo = :tipo,
                fecha_modificacion = :fecha_modificacion,
                pregunta_id = :pregunta_id,
                juego_id = :juego_id
            WHERE id_respuesta = :id_respuesta
        """),
        {
            'respuesta': respuesta,
            'tipo': tipo,
            'fecha_modificacion': fecha_modificacion,
            'pregunta_id': pregunta_id,
            'juego_id': juego_id,
            'id_respuesta': id_respuesta
        }
    )

    db.session.commit()