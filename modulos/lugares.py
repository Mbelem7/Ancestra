from app import db
from sqlalchemy import text


def insertar_lugar(nombre, descripcion, direccion, fecha_creacion,
                   fecha_modificacion, administrador_id, estado, contacto,
                   latitud, longitud):

    resultado = db.session.execute(
        text("""
            INSERT INTO lugar
            (
                nombre,
                descripcion,
                direccion,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado,
                contacto,
                latitud,
                longitud
            )
            VALUES
            (
                :nombre,
                :descripcion,
                :direccion,
                :fecha_creacion,
                :fecha_modificacion,
                :administrador_id,
                :estado,
                :contacto,
                :latitud,
                :longitud
            )
            RETURNING id_lugar
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'direccion': direccion,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'administrador_id': administrador_id,
            'estado': estado,
            'contacto': contacto,
            'latitud': latitud,
            'longitud': longitud
        }
    )

    id_lugar = resultado.scalar()

    db.session.commit()

    return id_lugar


def obtener_lugares(solo_activos=True):
    # solo_activos: si es True, no trae los lugares inactivos (quedan como dato histórico)
    filtro_estado = "WHERE estado = 'activo'" if solo_activos else ""

    resultado = db.session.execute(
        text(f"""
            SELECT
                id_lugar,
                nombre,
                descripcion,
                direccion,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado,
                contacto,
                latitud,
                longitud
            FROM lugar
            {filtro_estado}
        """)
    )

    lugares = resultado.fetchall()

    return lugares


def obtener_un_lugar(id_lugar):

    resultado = db.session.execute(
        text("""
            SELECT
                id_lugar,
                nombre,
                descripcion,
                direccion,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado,
                contacto,
                latitud,
                longitud
            FROM lugar
            WHERE id_lugar = :id_lugar
        """),
        {
            'id_lugar': id_lugar
        }
    )

    lugar = resultado.fetchone()

    return lugar


def obtener_lugares_por_nombre(nombre, solo_activos=True):
    # Para la búsqueda (barra de búsqueda del mapa)
    filtro_estado = "AND estado = 'activo'" if solo_activos else ""

    resultado = db.session.execute(
        text(f"""
            SELECT
                id_lugar,
                nombre,
                descripcion,
                direccion,
                fecha_creacion,
                fecha_modificacion,
                administrador_id,
                estado,
                contacto,
                latitud,
                longitud
            FROM lugar
            WHERE nombre ILIKE :nombre
            {filtro_estado}
        """),
        {
            'nombre': f"%{nombre}%"
        }
    )

    lugares = resultado.fetchall()

    return lugares


def actualizar_lugar(
    id_lugar,
    nombre,
    descripcion,
    direccion,
    fecha_modificacion,
    administrador_id,
    estado,
    contacto,
    latitud,
    longitud
):

    db.session.execute(
        text("""
            UPDATE lugar
            SET
                nombre = :nombre,
                descripcion = :descripcion,
                direccion = :direccion,
                fecha_modificacion = :fecha_modificacion,
                administrador_id = :administrador_id,
                estado = :estado,
                contacto = :contacto,
                latitud = :latitud,
                longitud = :longitud
            WHERE id_lugar = :id_lugar
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'direccion': direccion,
            'fecha_modificacion': fecha_modificacion,
            'administrador_id': administrador_id,
            'estado': estado,
            'contacto': contacto,
            'latitud': latitud,
            'longitud': longitud,
            'id_lugar': id_lugar
        }
    )

    db.session.commit()