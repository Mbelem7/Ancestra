from app import db
from sqlalchemy import text


# Los datos nuevos del registro (nivel, centro de trabajo, área, municipio y departamento) van SIEMPRE al final
# de cada consulta, para que las posiciones que ya usan las pantallas (d[0], d[1]... d[9]) no cambien.
# Los docentes que se registraron antes de este cambio tienen esos datos vacíos (None).

_UBICACION = """
            LEFT JOIN municipio mu ON mu.id_municipio = d.municipio_id
            LEFT JOIN departamento de ON de.id_departamento = mu.departamento_id
"""


def insertar_docente(persona_id, estado_verificacion, nivel_educativo=None,
                     centro_trabajo=None, area=None, municipio_id=None):

    resultado = db.session.execute(
        text("""
            INSERT INTO docente
            (
                persona_id,
                estado_verificacion,
                nivel_educativo,
                centro_trabajo,
                area,
                municipio_id
            )
            VALUES
            (
                :persona_id,
                :estado_verificacion,
                :nivel_educativo,
                :centro_trabajo,
                :area,
                :municipio_id
            )
            RETURNING id_docente
        """),
        {
            'persona_id': persona_id,
            'estado_verificacion': estado_verificacion,
            'nivel_educativo': nivel_educativo,
            'centro_trabajo': centro_trabajo,
            'area': area,
            'municipio_id': municipio_id
        }
    )

    id_docente = resultado.scalar()

    db.session.commit()

    return id_docente


def obtener_docentes():
    # Devuelve: (id_docente, estado_verificacion, id_persona, nombre_1, nombre_2, apellido_1, apellido_2,
    #            fecha_nacimiento, correo, estado,
    #            nivel_educativo, centro_trabajo, area, municipio, departamento)

    resultado = db.session.execute(
        text(f"""
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
                p.estado,
                d.nivel_educativo,
                d.centro_trabajo,
                d.area,
                mu.nombre,
                de.nombre
            FROM docente d
            INNER JOIN persona p ON p.id_persona = d.persona_id
            {_UBICACION}
        """)
    )

    docentes = resultado.fetchall()

    return docentes


def obtener_docentes_por_verificacion(estado_verificacion):
    # Para que el administrador vea, por ejemplo, los docentes pendientes
    # Devuelve las mismas columnas que obtener_docentes()

    resultado = db.session.execute(
        text(f"""
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
                p.estado,
                d.nivel_educativo,
                d.centro_trabajo,
                d.area,
                mu.nombre,
                de.nombre
            FROM docente d
            INNER JOIN persona p ON p.id_persona = d.persona_id
            {_UBICACION}
            WHERE d.estado_verificacion = :estado_verificacion
        """),
        {
            'estado_verificacion': estado_verificacion
        }
    )

    docentes = resultado.fetchall()

    return docentes


def obtener_un_docente(id_docente):
    # Devuelve las mismas columnas que obtener_docentes()

    resultado = db.session.execute(
        text(f"""
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
                p.estado,
                d.nivel_educativo,
                d.centro_trabajo,
                d.area,
                mu.nombre,
                de.nombre
            FROM docente d
            INNER JOIN persona p ON p.id_persona = d.persona_id
            {_UBICACION}
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


def obtener_docente_detalle(id_docente):
    # Todos los datos de un docente (su perfil y los datos personales con los que se registró).
    # Devuelve: (id_docente, estado_verificacion, id_persona, nombre_1, nombre_2, apellido_1,
    #            apellido_2, fecha_nacimiento, correo, estado, fecha_creacion,
    #            nivel_educativo, centro_trabajo, area, municipio, departamento)

    resultado = db.session.execute(
        text(f"""
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
                p.estado,
                p.fecha_creacion,
                d.nivel_educativo,
                d.centro_trabajo,
                d.area,
                mu.nombre,
                de.nombre
            FROM docente d
            INNER JOIN persona p ON p.id_persona = d.persona_id
            {_UBICACION}
            WHERE d.id_docente = :id_docente
        """),
        {
            'id_docente': id_docente
        }
    )

    docente = resultado.fetchone()

    return docente