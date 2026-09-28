from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy 
from dotenv import load_dotenv
import os
from modulos.archivos import *
from modulos.categorias import *
from modulos.juegos import *
from modulos.plantillas import *
from modulos.preguntas import *
from modulos.respuestas import * 
from modulos.resultados import *
from modulos.alianza import *
from modulos.autor import *
from modulos.persona import *
from modulos.docente import *
from modulos.estudiante import *
from modulos.lugares import *
from modulos.ruta import *

app = Flask(__name__)

load_dotenv()


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app) 

#PAGINA PRINCIPAL
@app.route("/")
def index():
    return render_template("index.html")

#CONECCION A LA BASE DE DATOS
from sqlalchemy import text

@app.route('/test-conexion')
def test_conexion():
    try:

        db.session.execute(text('SELECT 1'))
        return "¡Todo nítido, rey! 🚀 Conexión a Supabase exitosa."
    except Exception as e:
        return f"Error en la conexión: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)