from app import db
from sqlalchemy import text


def insertar_docente(persona_id, estado_verificacion):

    resultado = db.session.execute(
        text("""
            INSERT INTO docente
            (
                persona_id,
                estado_verificacion
            )
            VALUES
            (
                :persona_id,
                :estado_verificacion
            )
            RETURNING id_docente
        """),
        {
            'persona_id': persona_id,
            'estado_verificacion': estado_verificacion
        }
    )

    id_docente = resultado.scalar()

    db.session.commit()

    return id_docente


def obtener_docentes():

    resultado = db.session.execute(
        text("""
            SELECT
                d.id_docente,
                d.estado_verificacion,
                p.id_persona,
                p.nombre_1,
                p.nombre_2,
                p.apellido_1,
                p.apellido_2,
                p.fecha_nacimiento,
                p.correo,
                p.estado
            FROM docente d
            INNER JOIN persona p ON p.id_persona = d.persona_id
        """)
    )

    docentes = resultado.fetchall()

    return docentes


def obtener_docentes_por_verificacion(estado_verificacion):
    # Para que el administrador vea, por ejemplo, los docentes pendientes

    resultado = db.session.execute(
        text("""
            SELECT
                d.id_docente,
                d.estado_verificacion,
                p.id_persona,
                p.nombre_1,
                p.nombre_2,
                p.apellido_1,
                p.apellido_2,
                p.fecha_nacimiento,
                p.correo,
                p.estado
            FROM docente d
            INNER JOIN persona p ON p.id_persona = d.persona_id
            WHERE d.estado_verificacion = :estado_verificacion
        """),
        {
            'estado_verificacion': estado_verificacion
        }
    )

    docentes = resultado.fetchall()

    return docentes


def obtener_un_docente(id_docente):

    resultado = db.session.execute(
        text("""
            SELECT
                d.id_docente,
                d.estado_verificacion,
                p.id_persona,
                p.nombre_1,
                p.nombre_2,
                p.apellido_1,
                p.apellido_2,
                p.fecha_nacimiento,
                p.correo,
                p.estado
            FROM docente d
            INNER JOIN persona p ON p.id_persona = d.persona_id
            WHERE d.id_docente = :id_docente
        """),
        {
            'id_docente': id_docente
        }
    )

    docente = resultado.fetchone()

    return docente


def obtener_docente_por_persona(persona_id):
    # Para saber qué docente es la persona que inició sesión

    resultado = db.session.execute(
        text("""
            SELECT
                id_docente,
                estado_verificacion,
                persona_id
            FROM docente
            WHERE persona_id = :persona_id
        """),
        {
            'persona_id': persona_id
        }
    )

    docente = resultado.fetchone()

    return docente


def actualizar_estado_verificacion(id_docente, estado_verificacion):

    db.session.execute(
        text("""
            UPDATE docente
            SET
                estado_verificacion = :estado_verificacion
            WHERE id_docente = :id_docente
        """),
        {
            'estado_verificacion': estado_verificacion,
            'id_docente': id_docente
        }
    )

    db.session.commit()