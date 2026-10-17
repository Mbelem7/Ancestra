from app import db
from sqlalchemy import text


def insertar_persona(nombre_1, nombre_2, apellido_1, apellido_2,
                     fecha_nacimiento, correo, tipo, estado, contrasena,
                     fecha_creacion, fecha_modificacion):
    # contrasena debe llegar ya encriptada (hash), nunca en texto plano

    resultado = db.session.execute(
        text("""
            INSERT INTO persona
            (
                nombre_1,
                nombre_2,
                apellido_1,
                apellido_2,
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
                :nombre_1,
                :nombre_2,
                :apellido_1,
                :apellido_2,
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
            'nombre_1': nombre_1,
            'nombre_2': nombre_2,
            'apellido_1': apellido_1,
            'apellido_2': apellido_2,
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
                nombre_1,
                nombre_2,
                apellido_1,
                apellido_2,
                fecha_nacimiento,
                correo,
                tipo,
                estado,
                fecha_creacion,
                fecha_modificacion
            FROM persona
        """)
    )

    personas = resultado.fetchall()

    return personas


def obtener_una_persona(id_persona):

    resultado = db.session.execute(
        text("""
            SELECT
                id_persona,
                nombre_1,
                nombre_2,
                apellido_1,
                apellido_2,
                fecha_nacimiento,
                correo,
                tipo,
                estado,
                fecha_creacion,
                fecha_modificacion
            FROM persona
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
                nombre_1,
                apellido_1,
                correo,
                tipo,
                estado,
                contraseña,
                fecha_creacion,
                fecha_modificacion
            FROM persona
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
    nombre_1,
    nombre_2,
    apellido_1,
    apellido_2,
    fecha_nacimiento,
    correo,
    tipo,
    estado,
    fecha_modificacion
):

    db.session.execute(
        text("""
            UPDATE persona
            SET
                nombre_1 = :nombre_1,
                nombre_2 = :nombre_2,
                apellido_1 = :apellido_1,
                apellido_2 = :apellido_2,
                fecha_nacimiento = :fecha_nacimiento,
                correo = :correo,
                tipo = :tipo,
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_persona = :id_persona
        """),
        {
            'nombre_1': nombre_1,
            'nombre_2': nombre_2,
            'apellido_1': apellido_1,
            'apellido_2': apellido_2,
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
            UPDATE persona
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


def eliminar_persona(id_persona):
    # Solo se usa para deshacer un registro que quedó a medias
    # (se creó la persona pero falló la creación de su perfil de docente o estudiante)

    db.session.execute(
        text("""
            DELETE FROM persona
            WHERE id_persona = :id_persona
        """),
        {
            'id_persona': id_persona
        }
    )

    db.session.commit()

def obtener_contrasena_por_id(id_persona):
    # El hash de la contraseña de una persona, para comprobar la contraseña actual cuando quiere cambiarla

    resultado = db.session.execute(
        text("""
            SELECT contraseña
            FROM persona
            WHERE id_persona = :id_persona
        """),
        {
            'id_persona': id_persona
        }
    )

    fila = resultado.fetchone()

    return fila[0] if fila else None


def obtener_personas_para_aviso_caducidad(fecha_limite):
    # Personas activas que cambiaron su contraseña en esa fecha o antes (ya están en la ventana de avisos o vencidas).
    # fecha_modificacion se actualiza al cambiar la contraseña (y es igual a fecha_creacion en una cuenta nueva).
    # Devuelve: (id_persona, nombre_1, apellido_1, correo, ultimo_cambio)

    resultado = db.session.execute(
        text("""
            SELECT
                id_persona,
                nombre_1,
                apellido_1,
                correo,
                COALESCE(fecha_modificacion, fecha_creacion) AS ultimo_cambio
            FROM persona
            WHERE estado = 'activo'
              AND COALESCE(fecha_modificacion, fecha_creacion) <= :fecha_limite
            ORDER BY ultimo_cambio
        """),
        {
            'fecha_limite': fecha_limite
        }
    )

    personas = resultado.fetchall()

    return personas