from app import db
from sqlalchemy import text


def insertar_resultado(puntaje, fecha_creacion, fecha_modificacion,
                       respuesta_id, juego_id, estudiante_id):

    db.session.execute(
        text("""
            INSERT INTO resultado
            (
                puntaje,
                fecha_creacion,
                fecha_modificacion,
                respuesta_id,
                juego_id,
                estudiante_id
            )
            VALUES
            (
                :puntaje,
                :fecha_creacion,
                :fecha_modificacion,
                :respuesta_id,
                :juego_id,
                :estudiante_id
            )
        """),
        {
            'puntaje': puntaje,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
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
                fecha_modificacion,
                respuesta_id,
                juego_id,
                estudiante_id
            FROM resultado
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
                fecha_modificacion,
                respuesta_id,
                juego_id,
                estudiante_id
            FROM resultado
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
                pe.nombre_1,
                pe.apellido_1
            FROM resultado r
            INNER JOIN plantilla pl ON pl.juego_id = r.juego_id
            INNER JOIN juego j ON j.id_juego = r.juego_id
            INNER JOIN estudiante e ON e.id_estudiante = r.estudiante_id
            INNER JOIN persona pe ON pe.id_persona = e.persona_id
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
                fecha_modificacion,
                respuesta_id,
                juego_id,
                estudiante_id
            FROM resultado
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
    fecha_modificacion,
    respuesta_id
):

    db.session.execute(
        text("""
            UPDATE resultado
            SET
                puntaje = :puntaje,
                fecha_modificacion = :fecha_modificacion,
                respuesta_id = :respuesta_id
            WHERE id_resultado = :id_resultado
        """),
        {
            'puntaje': puntaje,
            'fecha_modificacion': fecha_modificacion,
            'respuesta_id': respuesta_id,
            'id_resultado': id_resultado
        }
    )

    db.session.commit()

    
def obtener_intentos_por_juego(juego_id):
    # Un INTENTO son todas las filas de resultado que un estudiante guardó con la misma fecha
    # (se guarda una fila por pregunta). Devuelve UNA fila por intento:
    #   (estudiante_id, nombre_1, nombre_2, apellido_1, apellido_2, correo,
    #    fecha, puntaje_total, cantidad_de_preguntas)

    resultado = db.session.execute(
        text("""
            SELECT
                r.estudiante_id,
                p.nombre_1,
                p.nombre_2,
                p.apellido_1,
                p.apellido_2,
                p.correo,
                r.fecha_creacion,
                SUM(r.puntaje) AS puntaje_total,
                COUNT(*) AS preguntas
            FROM resultado r
            INNER JOIN estudiante e ON e.id_estudiante = r.estudiante_id
            INNER JOIN persona p ON p.id_persona = e.persona_id
            WHERE r.juego_id = :juego_id
            GROUP BY
                r.estudiante_id,
                p.nombre_1,
                p.nombre_2,
                p.apellido_1,
                p.apellido_2,
                p.correo,
                r.fecha_creacion
            ORDER BY r.estudiante_id, r.fecha_creacion
        """),
        {
            'juego_id': juego_id
        }
    )

    intentos = resultado.fetchall()

    return intentos


def obtener_intentos_por_estudiante(estudiante_id):
    # Los intentos de UN estudiante en todas las plantillas que ha hecho.
    # Devuelve UNA fila por intento:
    #   (juego_id, nombre_del_juego, tipo, fecha, puntaje_total, cantidad_de_preguntas)

    resultado = db.session.execute(
        text("""
            SELECT
                r.juego_id,
                j.nombre,
                j.tipo,
                r.fecha_creacion,
                SUM(r.puntaje) AS puntaje_total,
                COUNT(*) AS preguntas
            FROM resultado r
            INNER JOIN juego j ON j.id_juego = r.juego_id
            WHERE r.estudiante_id = :estudiante_id
            GROUP BY
                r.juego_id,
                j.nombre,
                j.tipo,
                r.fecha_creacion
            ORDER BY r.fecha_creacion DESC
        """),
        {
            'estudiante_id': estudiante_id
        }
    )

    intentos = resultado.fetchall()

    return intentos


def obtener_resultados_de_estudiante_en_juego(estudiante_id, juego_id):
    # Las filas de resultado (una por pregunta) que un estudiante tiene en una plantilla.
    # Sirve para saber si ya hizo la evaluación y para revisar lo que respondió.
    # Devuelve: (id_resultado, puntaje, fecha_creacion, fecha_modificacion, respuesta_id)

    resultado = db.session.execute(
        text("""
            SELECT
                id_resultado,
                puntaje,
                fecha_creacion,
                fecha_modificacion,
                respuesta_id,
                respuesta_texto
            FROM resultado
            WHERE estudiante_id = :estudiante_id
              AND juego_id = :juego_id
            ORDER BY fecha_creacion, id_resultado
        """),
        {
            'estudiante_id': estudiante_id,
            'juego_id': juego_id
        }
    )

    filas = resultado.fetchall()

    return filas


def registrar_respuesta_en_resultado(id_resultado, puntaje, respuesta_id, fecha_modificacion, respuesta_texto=None):
    # Guarda la respuesta y el puntaje de UNA pregunta, en la fila que se creó al abrir la evaluación.
    # respuesta_texto es lo que escribió el estudiante (solo en "Completar"; en los demás juegos queda vacío)

    db.session.execute(
        text("""
            UPDATE resultado
            SET
                puntaje = :puntaje,
                respuesta_id = :respuesta_id,
                respuesta_texto = :respuesta_texto,
                fecha_modificacion = :fecha_modificacion
            WHERE id_resultado = :id_resultado
        """),
        {
            'puntaje': puntaje,
            'respuesta_id': respuesta_id,
            'respuesta_texto': respuesta_texto,
            'fecha_modificacion': fecha_modificacion,
            'id_resultado': id_resultado
        }
    )

    db.session.commit()