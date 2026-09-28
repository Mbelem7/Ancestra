from app import db
from sqlalchemy import text

def mostrar_categorias():

    resultado = db.session.execute(
        text("""
            SELECT
                id_categoria,
                nombre
            FROM categoria
        """)
    )

    categorias = resultado.fetchall()

    return categorias