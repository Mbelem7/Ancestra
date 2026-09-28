from app import db
from sqlalchemy import text


def insertar_persona(nombre1, nombre2, apellido1, apellido2,
                     fecha_nacimiento, correo, tipo, estado, contrasena,
                     fecha_creacion, fecha_modificacion):
    # contrasena debe llegar ya encriptada (hash), nunca en texto plano

    resultado = db.session.execute(
        text("""
            INSERT INTO PERSONA
            (
                nombre1,
                nombre2,
                apellido1,
                apellido2,
                fecha_nacimiento,
                correo,
                tipo,
                estado,
                contraseña,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :nombre1,
                :nombre2,
                :apellido1,
                :apellido2,
                :fecha_nacimiento,
                :correo,
                :tipo,
                :estado,
                :contrasena,
                :fecha_creacion,
                :fecha_modificacion
            )
            RETURNING id_persona
        """),
        {
            'nombre1': nombre1,
            'nombre2': nombre2,
            'apellido1': apellido1,
            'apellido2': apellido2,
            'fecha_nacimiento': fecha_nacimiento,
            'correo': correo,
            'tipo': tipo,
            'estado': estado,
            'contrasena': contrasena,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion
        }
    )

    id_persona = resultado.scalar()

    db.session.commit()

    return id_persona


def obtener_personas():
    # No se devuelve la contraseña

    resultado = db.session.execute(
        text("""
            SELECT
                id_persona,
                nombre1,
                nombre2,
                apellido1,
                apellido2,
                fecha_nacimiento,
                correo,
                tipo,
                estado,
                fecha_creacion,
                fecha_modificacion
            FROM PERSONA
        """)
    )

    personas = resultado.fetchall()

    return personas


def obtener_una_persona(id_persona):

    resultado = db.session.execute(
        text("""
            SELECT
                id_persona,
                nombre1,
                nombre2,
                apellido1,
                apellido2,
                fecha_nacimiento,
                correo,
                tipo,
                estado,
                fecha_creacion,
                fecha_modificacion
            FROM PERSONA
            WHERE id_persona = :id_persona
        """),
        {
            'id_persona': id_persona
        }
    )

    persona = resultado.fetchone()

    return persona


def obtener_persona_por_correo(correo):
    # Para el login: aquí SÍ se devuelve la contraseña (hash) para compararla

    resultado = db.session.execute(
        text("""
            SELECT
                id_persona,
                nombre1,
                apellido1,
                correo,
                tipo,
                estado,
                contraseña
            FROM PERSONA
            WHERE correo = :correo
        """),
        {
            'correo': correo
        }
    )

    persona = resultado.fetchone()

    return persona


def actualizar_persona(
    id_persona,
    nombre1,
    nombre2,
    apellido1,
    apellido2,
    fecha_nacimiento,
    correo,
    tipo,
    estado,
    fecha_modificacion
):

    db.session.execute(
        text("""
            UPDATE PERSONA
            SET
                nombre1 = :nombre1,
                nombre2 = :nombre2,
                apellido1 = :apellido1,
                apellido2 = :apellido2,
                fecha_nacimiento = :fecha_nacimiento,
                correo = :correo,
                tipo = :tipo,
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_persona = :id_persona
        """),
        {
            'nombre1': nombre1,
            'nombre2': nombre2,
            'apellido1': apellido1,
            'apellido2': apellido2,
            'fecha_nacimiento': fecha_nacimiento,
            'correo': correo,
            'tipo': tipo,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion,
            'id_persona': id_persona
        }
    )

    db.session.commit()


def actualizar_contrasena(id_persona, contrasena, fecha_modificacion):
    # contrasena debe llegar ya encriptada (hash)

    db.session.execute(
        text("""
            UPDATE PERSONA
            SET
                contraseña = :contrasena,
                fecha_modificacion = :fecha_modificacion
            WHERE id_persona = :id_persona
        """),
        {
            'contrasena': contrasena,
            'fecha_modificacion': fecha_modificacion,
            'id_persona': id_persona
        }
    )

    db.session.commit()