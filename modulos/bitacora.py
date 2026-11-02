from app import db
from sqlalchemy import text


# ======================================================================
# Bitácora de accesos
# Rama 1 · Política 3 · Control 3.1.1 (registro de actividad diaria) y Control 2.3.1 (contención de intentos)
# ======================================================================

def insertar_evento_bitacora(persona_id, correo, evento, ip, navegador, fecha):

    db.session.execute(
        text("""
            INSERT INTO bitacora_acceso
            (
                persona_id,
                correo,
                evento,
                ip,
                navegador,
                fecha
            )
            VALUES
            (
                :persona_id,
                :correo,
                :evento,
                :ip,
                :navegador,
                :fecha
            )
        """),
        {
            'persona_id': persona_id,
            'correo': correo,
            'evento': evento,
            'ip': ip,
            'navegador': navegador,
            'fecha': fecha
        }
    )

    db.session.commit()


def obtener_fallidos_recientes(correo, desde, limite):
    # Las fechas de los intentos fallidos con ese correo desde "desde", sin contar los anteriores a su último
    # inicio de sesión correcto (entrar bien "limpia" los intentos). Del más reciente al más antiguo.

    resultado = db.session.execute(
        text("""
            SELECT fecha
            FROM bitacora_acceso
            WHERE correo = :correo
              AND evento = 'intento_fallido'
              AND fecha >= :desde
              AND fecha > COALESCE(
                    (SELECT MAX(fecha) FROM bitacora_acceso
                     WHERE correo = :correo AND evento = 'inicio_sesion'),
                    '-infinity'::timestamp)
            ORDER BY fecha DESC
            LIMIT :limite
        """),
        {
            'correo': correo,
            'desde': desde,
            'limite': limite
        }
    )

    return [fila[0] for fila in resultado.fetchall()]


def obtener_bitacora(limite, evento=None, correo=None):
    # Los eventos más recientes, con el nombre de la persona si el correo corresponde a una cuenta.
    # Devuelve: (id_bitacora, fecha, evento, correo, ip, navegador, nombre_1, apellido_1, tipo)
    condiciones = []
    parametros = {'limite': limite}
    if evento:
        condiciones.append("b.evento = :evento")
        parametros['evento'] = evento
    if correo:
        condiciones.append("b.correo ILIKE :correo")
        parametros['correo'] = f"%{correo}%"
    # Solo se insertan estos trozos fijos; lo que escribe el administrador viaja como parámetro
    donde = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    resultado = db.session.execute(
        text(f"""
            SELECT
                b.id_bitacora,
                b.fecha,
                b.evento,
                b.correo,
                b.ip,
                b.navegador,
                p.nombre_1,
                p.apellido_1,
                p.tipo
            FROM bitacora_acceso b
            LEFT JOIN persona p ON p.id_persona = b.persona_id
            {donde}
            ORDER BY b.fecha DESC
            LIMIT :limite
        """),
        parametros
    )

    return resultado.fetchall()


def resumen_bitacora(desde):
    # Cuántos eventos de cada tipo hubo desde esa fecha. Devuelve: (evento, cantidad)

    resultado = db.session.execute(
        text("""
            SELECT evento, COUNT(*)
            FROM bitacora_acceso
            WHERE fecha >= :desde
            GROUP BY evento
        """),
        {
            'desde': desde
        }
    )

    return resultado.fetchall()