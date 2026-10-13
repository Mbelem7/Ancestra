from app import db
from sqlalchemy import text


def insertar_plantilla(codigo_acceso, fecha_creacion, fecha_modificacion,
                       juego_id, docente_id, administrador_id):

    resultado = db.session.execute(
        text("""
            INSERT INTO plantilla
            (
                codigo_acceso,
                fecha_creacion,
                fecha_modificacion,
                juego_id,
                docente_id,
                administrador_id
            )
            VALUES
            (
                :codigo_acceso,
                :fecha_creacion,
                :fecha_modificacion,
                :juego_id,
                :docente_id,
                :administrador_id
            )
            RETURNING id_plantilla
        """),
        {
            'codigo_acceso': codigo_acceso,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'juego_id': juego_id,
            'docente_id': docente_id,
            'administrador_id': administrador_id
        }
    )

    id_plantilla = resultado.scalar()

    db.session.commit()

    return id_plantilla


def obtener_plantillas():

    resultado = db.session.execute(
        text("""
            SELECT
                id_plantilla,
                codigo_acceso,
                fecha_creacion,
                fecha_modificacion,
                juego_id,
                docente_id,
                administrador_id
            FROM plantilla
        """)
    )

    plantillas = resultado.fetchall()

    return plantillas


def obtener_plantillas_por_docente(docente_id):

    resultado = db.session.execute(
        text("""
            SELECT
                p.id_plantilla,
                p.codigo_acceso,
                p.fecha_creacion,
                p.fecha_modificacion,
                p.juego_id,
                j.nombre,
                j.descripcion,
                p.docente_id,
                p.administrador_id
            FROM plantilla p
            INNER JOIN juego j ON j.id_juego = p.juego_id
            WHERE p.docente_id = :docente_id
        """),
        {
            'docente_id': docente_id
        }
    )

    plantillas = resultado.fetchall()

    return plantillas


def obtener_una_plantilla(id_plantilla):

    resultado = db.session.execute(
        text("""
            SELECT
                id_plantilla,
                codigo_acceso,
                fecha_creacion,
                fecha_modificacion,
                juego_id,
                docente_id,
                administrador_id
            FROM plantilla
            WHERE id_plantilla = :id_plantilla
        """),
        {
            'id_plantilla': id_plantilla
        }
    )

    plantilla = resultado.fetchone()

    return plantilla


def obtener_plantilla_por_codigo(codigo_acceso):
    # Cuando el estudiante ingresa el código que le dio el docente

    resultado = db.session.execute(
        text("""
            SELECT
                id_plantilla,
                codigo_acceso,
                fecha_creacion,
                fecha_modificacion,
                juego_id,
                docente_id,
                administrador_id
            FROM plantilla
            WHERE codigo_acceso = :codigo_acceso
        """),
        {
            'codigo_acceso': codigo_acceso
        }
    )

    plantilla = resultado.fetchone()

    return plantilla


def actualizar_plantilla(
    id_plantilla,
    codigo_acceso,
    fecha_modificacion,
    juego_id,
    docente_id,
    administrador_id
):

    db.session.execute(
        text("""
            UPDATE plantilla
            SET
                codigo_acceso = :codigo_acceso,
                fecha_modificacion = :fecha_modificacion,
                juego_id = :juego_id,
                docente_id = :docente_id,
                administrador_id = :administrador_id
            WHERE id_plantilla = :id_plantilla
        """),
        {
            'codigo_acceso': codigo_acceso,
            'fecha_modificacion': fecha_modificacion,
            'juego_id': juego_id,
            'docente_id': docente_id,
            'administrador_id': administrador_id,
            'id_plantilla': id_plantilla
        }
    )

    db.session.commit()


def obtener_plantillas_resumen(docente_id=None):
    # Lista las plantillas con el nombre y el tipo de su juego, y cuántas preguntas tienen.
    # Sin docente_id trae todas (mientras no haya login); con docente_id solo las de ese docente.

    consulta = """
        SELECT
            p.id_plantilla,
            p.codigo_acceso,
            p.fecha_creacion,
            j.nombre,
            j.descripcion,
            j.tipo,
            j.estado,
            (SELECT COUNT(*) FROM pregunta pr WHERE pr.plantilla_id = p.id_plantilla) AS total_preguntas
        FROM plantilla p
        INNER JOIN juego j ON j.id_juego = p.juego_id
    """
    parametros = {}

    if docente_id is not None:
        consulta += " WHERE p.docente_id = :docente_id"
        parametros['docente_id'] = docente_id

    consulta += " ORDER BY p.id_plantilla DESC"

    resultado = db.session.execute(text(consulta), parametros)

    plantillas = resultado.fetchall()

    return plantillas