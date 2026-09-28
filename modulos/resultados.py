from app import db
from sqlalchemy import text


def insertar_resultado(puntaje, fecha_creacion, respuesta_id,
                       juego_id, estudiante_id):

    db.session.execute(
        text("""
            INSERT INTO RESULTADO
            (
                puntaje,
                fecha_creacion,
                respuesta_id,
                juego_id,
                estudiante_id
            )
            VALUES
            (
                :puntaje,
                :fecha_creacion,
                :respuesta_id,
                :juego_id,
                :estudiante_id
            )
        """),
        {
            'puntaje': puntaje,
            'fecha_creacion': fecha_creacion,
            'respuesta_id': respuesta_id,
            'juego_id': juego_id,
            'estudiante_id': estudiante_id
        }
    )

    db.session.commit()


def obtener_resultados():

    resultado = db.session.execute(
        text("""
            SELECT
                id_resultado,
                puntaje,
                fecha_creacion,
                respuesta_id,
                juego_id,
                estudiante_id
            FROM RESULTADO
        """)
    )

    resultados = resultado.fetchall()

    return resultados


def obtener_resultados_por_estudiante(estudiante_id):

    resultado = db.session.execute(
        text("""
            SELECT
                id_resultado,
                puntaje,
                fecha_creacion,
                respuesta_id,
                juego_id,
                estudiante_id
            FROM RESULTADO
            WHERE estudiante_id = :estudiante_id
        """),
        {
            'estudiante_id': estudiante_id
        }
    )

    resultados = resultado.fetchall()

    return resultados


def obtener_resultados_por_docente(docente_id):
    # El docente ve las notas de todas sus evaluaciones

    resultado = db.session.execute(
        text("""
            SELECT
                r.id_resultado,
                r.puntaje,
                r.fecha_creacion,
                r.juego_id,
                j.nombre AS juego,
                r.estudiante_id,
                pe.nombre1,
                pe.apellido1
            FROM RESULTADO r
            INNER JOIN PLANTILLA pl ON pl.juego_id = r.juego_id
            INNER JOIN JUEGO j ON j.id_juego = r.juego_id
            INNER JOIN ESTUDIANTE e ON e.id_estudiante = r.estudiante_id
            INNER JOIN PERSONA pe ON pe.id_persona = e.persona_id
            WHERE pl.docente_id = :docente_id
        """),
        {
            'docente_id': docente_id
        }
    )

    resultados = resultado.fetchall()

    return resultados


def obtener_un_resultado(id_resultado):

    resultado = db.session.execute(
        text("""
            SELECT
                id_resultado,
                puntaje,
                fecha_creacion,
                respuesta_id,
                juego_id,
                estudiante_id
            FROM RESULTADO
            WHERE id_resultado = :id_resultado
        """),
        {
            'id_resultado': id_resultado
        }
    )

    resultado_unico = resultado.fetchone()

    return resultado_unico


def actualizar_resultado(
    id_resultado,
    puntaje,
    respuesta_id
):

    db.session.execute(
        text("""
            UPDATE RESULTADO
            SET
                puntaje = :puntaje,
                respuesta_id = :respuesta_id
            WHERE id_resultado = :id_resultado
        """),
        {
            'puntaje': puntaje,
            'respuesta_id': respuesta_id,
            'id_resultado': id_resultado
        }
    )

    db.session.commit()