from app import db
from sqlalchemy import text

def insertar_archivo(nombre, descripcion, URL, categoria, tipo,
                     fecha_creacion, fecha_modificacion,
                     administrador_id, estado):

    db.session.execute(
        text("""
            INSERT INTO ARCHIVOS
            (
                nombre,
                descripcion,
                URL,
                categoria_id,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            )
            VALUES
            (
                :nombre,
                :descripcion,
                :URL,
                :categoria,
                :tipo,
                :fecha_creacion,
                :fecha_modificacion,
                :administrador_id,
                :estado
            )
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'URL': URL,
            'categoria': categoria,
            'tipo': tipo,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'administrador_id': administrador_id,
            'estado': estado
        }
    )

    db.session.commit()

def obtener_archivos():

    resultado = db.session.execute(
        text("""
            SELECT
                id_archivo,
                nombre,
                descripcion,
                URL,
                categoria_id,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            FROM ARCHIVOS
        """)
    )

    archivos = resultado.fetchall()

    return archivos

def obtener_un_archivo(id_archivo):

    resultado = db.session.execute(
        text("""
            SELECT
                id_archivo,
                nombre,
                descripcion,
                URL,
                categoria_id,
                tipo,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado
            FROM ARCHIVOS
            WHERE id_archivo = :id_archivo
        """),
        {
            'id_archivo': id_archivo
        }
    )

    archivo = resultado.fetchone()

    return archivo

def actualizar_archivo(
    id_archivo,
    nombre,
    descripcion,
    URL,
    categoria_id,
    tipo,
    fecha_modificacion,
    administrador_id,
    estado
):

    db.session.execute(
        text("""
            UPDATE ARCHIVOS
            SET
                nombre = :nombre,
                descripcion = :descripcion,
                URL = :URL,
                categoria_id = :categoria_id,
                tipo = :tipo,
                fecha_modificacion = :fecha_modificacion,
                administrador_id = :administrador_id,
                estado = :estado
            WHERE id_archivo = :id_archivo
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'URL': URL,
            'categoria_id': categoria_id,
            'tipo': tipo,
            'fecha_modificacion': fecha_modificacion,
            'administrador_id': administrador_id,
            'estado': estado,
            'id_archivo': id_archivo
        }
    )

    db.session.commit()
    