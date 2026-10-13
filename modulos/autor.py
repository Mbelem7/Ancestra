from app import db
from sqlalchemy import text


# ======================================================================
# autor
# ======================================================================

def insertar_autor(nombre, tipo, origen, descripcion,
                   fecha_creacion, fecha_modificacion):

    resultado = db.session.execute(
        text("""
            INSERT INTO autor
            (
                nombre,
                tipo,
                origen,
                descripcion,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :nombre,
                :tipo,
                :origen,
                :descripcion,
                :fecha_creacion,
                :fecha_modificacion
            )
            RETURNING id_autor
        """),
        {
            'nombre': nombre,
            'tipo': tipo,
            'origen': origen,
            'descripcion': descripcion,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion
        }
    )

    id_autor = resultado.scalar()

    db.session.commit()

    return id_autor


def obtener_autores():

    resultado = db.session.execute(
        text("""
            SELECT
                id_autor,
                nombre,
                tipo,
                origen,
                descripcion,
                fecha_creacion,
                fecha_modificacion
            FROM autor
        """)
    )

    autores = resultado.fetchall()

    return autores


def obtener_un_autor(id_autor):

    resultado = db.session.execute(
        text("""
            SELECT
                id_autor,
                nombre,
                tipo,
                origen,
                descripcion,
                fecha_creacion,
                fecha_modificacion
            FROM autor
            WHERE id_autor = :id_autor
        """),
        {
            'id_autor': id_autor
        }
    )

    autor = resultado.fetchone()

    return autor


def actualizar_autor(
    id_autor,
    nombre,
    tipo,
    origen,
    descripcion,
    fecha_modificacion
):

    db.session.execute(
        text("""
            UPDATE autor
            SET
                nombre = :nombre,
                tipo = :tipo,
                origen = :origen,
                descripcion = :descripcion,
                fecha_modificacion = :fecha_modificacion
            WHERE id_autor = :id_autor
        """),
        {
            'nombre': nombre,
            'tipo': tipo,
            'origen': origen,
            'descripcion': descripcion,
            'fecha_modificacion': fecha_modificacion,
            'id_autor': id_autor
        }
    )

    db.session.commit()


# ======================================================================
# archivo_autor  (tabla intermedia archivo <-> autor)
# ======================================================================

def insertar_archivo_autor(archivo_id, autor_id):

    db.session.execute(
        text("""
            INSERT INTO archivo_autor
            (
                archivo_id,
                autor_id
            )
            VALUES
            (
                :archivo_id,
                :autor_id
            )
        """),
        {
            'archivo_id': archivo_id,
            'autor_id': autor_id
        }
    )

    db.session.commit()


def obtener_archivo_autores():

    resultado = db.session.execute(
        text("""
            SELECT
                id_archivoautor,
                archivo_id,
                autor_id
            FROM archivo_autor
        """)
    )

    relaciones = resultado.fetchall()

    return relaciones


def obtener_autores_por_archivo(archivo_id):
    # Todos los autores de un archivo

    resultado = db.session.execute(
        text("""
            SELECT
                a.id_autor,
                a.nombre,
                a.tipo,
                a.origen,
                a.descripcion
            FROM archivo_autor aa
            INNER JOIN autor a ON a.id_autor = aa.autor_id
            WHERE aa.archivo_id = :archivo_id
        """),
        {
            'archivo_id': archivo_id
        }
    )

    autores = resultado.fetchall()

    return autores


def obtener_archivos_por_autor(autor_id):
    # Todos los archivos de un autor

    resultado = db.session.execute(
        text("""
            SELECT
                ar.id_archivo,
                ar.nombre,
                ar.descripcion,
                ar.url,
                ar.categoria_id,
                ar.tipo,
                ar.estado
            FROM archivo_autor aa
            INNER JOIN archivo ar ON ar.id_archivo = aa.archivo_id
            WHERE aa.autor_id = :autor_id
        """),
        {
            'autor_id': autor_id
        }
    )

    archivos = resultado.fetchall()

    return archivos


def obtener_una_archivo_autor(id_archivoautor):

    resultado = db.session.execute(
        text("""
            SELECT
                id_archivoautor,
                archivo_id,
                autor_id
            FROM archivo_autor
            WHERE id_archivoautor = :id_archivoautor
        """),
        {
            'id_archivoautor': id_archivoautor
        }
    )

    relacion = resultado.fetchone()

    return relacion


def actualizar_archivo_autor(id_archivoautor, archivo_id, autor_id):

    db.session.execute(
        text("""
            UPDATE archivo_autor
            SET
                archivo_id = :archivo_id,
                autor_id = :autor_id
            WHERE id_archivoautor = :id_archivoautor
        """),
        {
            'archivo_id': archivo_id,
            'autor_id': autor_id,
            'id_archivoautor': id_archivoautor
        }
    )

    db.session.commit()


def eliminar_archivo_autor(id_archivoautor):
    # La tabla no tiene campo estado, así que aquí sí se borra la fila

    db.session.execute(
        text("""
            DELETE FROM archivo_autor
            WHERE id_archivoautor = :id_archivoautor
        """),
        {
            'id_archivoautor': id_archivoautor
        }
    )

    db.session.commit()