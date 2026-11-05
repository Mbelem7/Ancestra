from app import db
from sqlalchemy import text


# ======================================================================
# Configuración editable por el administrador
# ======================================================================

def obtener_configuracion():
    # Todos los parámetros como diccionario: {'intentos_maximos': '5', 'minutos_bloqueo': '15'}
    resultado = db.session.execute(text("SELECT clave, valor FROM configuracion"))
    return {clave: valor for clave, valor in resultado.fetchall()}


def actualizar_configuracion(clave, valor, fecha_modificacion):

    db.session.execute(
        text("""
            UPDATE configuracion
            SET valor = :valor, fecha_modificacion = :fecha_modificacion
            WHERE clave = :clave
        """),
        {'clave': clave, 'valor': valor, 'fecha_modificacion': fecha_modificacion}
    )

    db.session.commit()


# ======================================================================
# Auditoría de cambios (Rama 5 · Política 3 · Control 3.1.2: identificación de autoría de cambios)
# ======================================================================

def insertar_auditoria(tabla, registro, accion, detalle, persona_id, correo, ip, fecha):

    db.session.execute(
        text("""
            INSERT INTO auditoria (tabla, registro, accion, detalle, persona_id, correo, ip, fecha)
            VALUES (:tabla, :registro, :accion, :detalle, :persona_id, :correo, :ip, :fecha)
        """),
        {
            'tabla': tabla, 'registro': registro, 'accion': accion, 'detalle': detalle,
            'persona_id': persona_id, 'correo': correo, 'ip': ip, 'fecha': fecha
        }
    )

    db.session.commit()


def obtener_auditoria(tabla, limite):
    # Los cambios más recientes de una tabla, con el nombre de quien los hizo.
    # Devuelve: (fecha, registro, accion, detalle, correo, ip, nombre_1, apellido_1)

    resultado = db.session.execute(
        text("""
            SELECT
                a.fecha,
                a.registro,
                a.accion,
                a.detalle,
                a.correo,
                a.ip,
                p.nombre_1,
                p.apellido_1
            FROM auditoria a
            LEFT JOIN persona p ON p.id_persona = a.persona_id
            WHERE a.tabla = :tabla
            ORDER BY a.fecha DESC
            LIMIT :limite
        """),
        {'tabla': tabla, 'limite': limite}
    )

    return resultado.fetchall()


def obtener_auditoria_reciente(limite):
    # Los cambios más recientes en el contenido de la plataforma (todo menos la configuración, que tiene su propio historial).
    # Devuelve: (fecha, tabla, registro, accion, detalle, correo, ip, nombre_1, apellido_1)

    resultado = db.session.execute(
        text("""
            SELECT
                a.fecha,
                a.tabla,
                a.registro,
                a.accion,
                a.detalle,
                a.correo,
                a.ip,
                p.nombre_1,
                p.apellido_1
            FROM auditoria a
            LEFT JOIN persona p ON p.id_persona = a.persona_id
            WHERE a.tabla <> 'configuracion'
            ORDER BY a.fecha DESC
            LIMIT :limite
        """),
        {'limite': limite}
    )

    return resultado.fetchall()