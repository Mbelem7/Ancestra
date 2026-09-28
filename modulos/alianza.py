from app import db
from sqlalchemy import text

def insertar_alianza(lugar_id, administrador_id, estado, tipo_negocio,
                     monto_mensual, fecha_inicio, fecha_vencimiento,
                     fecha_creacion, fecha_modificacion):

    db.session.execute(
        text("""
            INSERT INTO ALIANZA
            (
                lugar_id,
                administrador_id,
                estado,
                tipo_negocio,
                monto_mensual,
                fecha_inicio,
                fecha_vencimiento,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :lugar_id,
                :administrador_id,
                :estado,
                :tipo_negocio,
                :monto_mensual,
                :fecha_inicio,
                :fecha_vencimiento,
                :fecha_creacion,
                :fecha_modificacion
            )
        """),
        {
            'lugar_id': lugar_id,
            'administrador_id': administrador_id,
            'estado': estado,
            'tipo_negocio': tipo_negocio,
            'monto_mensual': monto_mensual,
            'fecha_inicio': fecha_inicio,
            'fecha_vencimiento': fecha_vencimiento,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def obtener_alianzas():

    resultado = db.session.execute(
        text("""
            SELECT
                id_alianza,
                lugar_id,
                administrador_id,
                estado,
                tipo_negocio,
                monto_mensual,
                fecha_inicio,
                fecha_vencimiento,
                fecha_creacion,
                fecha_modificacion
            FROM ALIANZA
        """)
    )

    alianzas = resultado.fetchall()

    return alianzas


def obtener_alianzas_por_lugar(lugar_id):

    resultado = db.session.execute(
        text("""
            SELECT
                id_alianza,
                lugar_id,
                administrador_id,
                estado,
                tipo_negocio,
                monto_mensual,
                fecha_inicio,
                fecha_vencimiento,
                fecha_creacion,
                fecha_modificacion
            FROM ALIANZA
            WHERE lugar_id = :lugar_id
        """),
        {
            'lugar_id': lugar_id
        }
    )

    alianzas = resultado.fetchall()

    return alianzas


def obtener_una_alianza(id_alianza):

    resultado = db.session.execute(
        text("""
            SELECT
                id_alianza,
                lugar_id,
                administrador_id,
                estado,
                tipo_negocio,
                monto_mensual,
                fecha_inicio,
                fecha_vencimiento,
                fecha_creacion,
                fecha_modificacion
            FROM ALIANZA
            WHERE id_alianza = :id_alianza
        """),
        {
            'id_alianza': id_alianza
        }
    )

    alianza = resultado.fetchone()

    return alianza


def actualizar_alianza(
    id_alianza,
    lugar_id,
    administrador_id,
    estado,
    tipo_negocio,
    monto_mensual,
    fecha_inicio,
    fecha_vencimiento,
    fecha_modificacion
):

    db.session.execute(
        text("""
            UPDATE ALIANZA
            SET
                lugar_id = :lugar_id,
                administrador_id = :administrador_id,
                estado = :estado,
                tipo_negocio = :tipo_negocio,
                monto_mensual = :monto_mensual,
                fecha_inicio = :fecha_inicio,
                fecha_vencimiento = :fecha_vencimiento,
                fecha_modificacion = :fecha_modificacion
            WHERE id_alianza = :id_alianza
        """),
        {
            'lugar_id': lugar_id,
            'administrador_id': administrador_id,
            'estado': estado,
            'tipo_negocio': tipo_negocio,
            'monto_mensual': monto_mensual,
            'fecha_inicio': fecha_inicio,
            'fecha_vencimiento': fecha_vencimiento,
            'fecha_modificacion': fecha_modificacion,
            'id_alianza': id_alianza
        }
    )

    db.session.commit()