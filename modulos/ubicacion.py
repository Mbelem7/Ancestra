from app import db
from sqlalchemy import text


# ======================================================================
# Departamentos, regiones autónomas y municipios de Nicaragua
# (Ley N.° 59 de División Política Administrativa, texto consolidado 2021)
# ======================================================================

def obtener_departamentos():
    # Primero los 15 departamentos y al final las 2 regiones autónomas, cada grupo en orden alfabético.
    # Devuelve: (id_departamento, nombre, tipo)

    resultado = db.session.execute(
        text("""
            SELECT
                id_departamento,
                nombre,
                tipo
            FROM departamento
            ORDER BY tipo, nombre
        """)
    )

    return resultado.fetchall()


def obtener_municipios():
    # Todos los municipios, con el departamento al que pertenecen
    # (el formulario de registro muestra solo los del departamento elegido).
    # Devuelve: (id_municipio, nombre, departamento_id)

    resultado = db.session.execute(
        text("""
            SELECT
                id_municipio,
                nombre,
                departamento_id
            FROM municipio
            ORDER BY nombre
        """)
    )

    return resultado.fetchall()


def obtener_un_municipio(id_municipio):
    # Un municipio con su departamento (para validar el registro y para mostrarlo).
    # Devuelve: (id_municipio, nombre_municipio, id_departamento, nombre_departamento)

    resultado = db.session.execute(
        text("""
            SELECT
                m.id_municipio,
                m.nombre,
                d.id_departamento,
                d.nombre
            FROM municipio m
            INNER JOIN departamento d ON d.id_departamento = m.departamento_id
            WHERE m.id_municipio = :id_municipio
        """),
        {
            'id_municipio': id_municipio
        }
    )

    return resultado.fetchone()