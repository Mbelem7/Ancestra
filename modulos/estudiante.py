from app import db
from sqlalchemy import text


# Los datos nuevos del registro (nivel, centro de estudio, municipio y departamento) van SIEMPRE al final
# de cada consulta, para que las posiciones que ya se usan (e[0], e[1]... e[8]) no cambien.
# Los estudiantes que se registraron antes de este cambio tienen esos datos vacíos (None).

_UBICACION = """
            LEFT JOIN municipio mu ON mu.id_municipio = e.municipio_id
            LEFT JOIN departamento de ON de.id_departamento = mu.departamento_id
"""


def insertar_estudiante(persona_id, estado, nivel_educativo=None,
                        centro_estudio=None, municipio_id=None):

    resultado = db.session.execute(
        text("""
            INSERT INTO estudiante
            (
                persona_id,
                estado,
                nivel_educativo,
                centro_estudio,
                municipio_id
            )
            VALUES
            (
                :persona_id,
                :estado,
                :nivel_educativo,
                :centro_estudio,
                :municipio_id
            )
            RETURNING id_estudiante
        """),
        {
            'persona_id': persona_id,
            'estado': estado,
            'nivel_educativo': nivel_educativo,
            'centro_estudio': centro_estudio,
            'municipio_id': municipio_id
        }
    )

    id_estudiante = resultado.scalar()

    db.session.commit()

    return id_estudiante


def obtener_estudiantes():
    # Devuelve: (id_estudiante, estado, id_persona, nombre_1, nombre_2, apellido_1, apellido_2,
    #            fecha_nacimiento, correo,
    #            nivel_educativo, centro_estudio, municipio, departamento)

    resultado = db.session.execute(
        text(f"""
            SELECT
                e.id_estudiante,
                e.estado,
                p.id_persona,
                p.nombre_1,
                p.nombre_2,
                p.apellido_1,
                p.apellido_2,
                p.fecha_nacimiento,
                p.correo,
                e.nivel_educativo,
                e.centro_estudio,
                mu.nombre,
                de.nombre
            FROM estudiante e
            INNER JOIN persona p ON p.id_persona = e.persona_id
            {_UBICACION}
        """)
    )

    estudiantes = resultado.fetchall()

    return estudiantes


def obtener_un_estudiante(id_estudiante):
    # Devuelve las mismas columnas que obtener_estudiantes()

    resultado = db.session.execute(
        text(f"""
            SELECT
                e.id_estudiante,
                e.estado,
                p.id_persona,
                p.nombre_1,
                p.nombre_2,
                p.apellido_1,
                p.apellido_2,
                p.fecha_nacimiento,
                p.correo,
                e.nivel_educativo,
                e.centro_estudio,
                mu.nombre,
                de.nombre
            FROM estudiante e
            INNER JOIN persona p ON p.id_persona = e.persona_id
            {_UBICACION}
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