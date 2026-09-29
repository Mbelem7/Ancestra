from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# MÓDULOS
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


# PÁGINA PRINCIPAL
@app.route("/")
def index():
    return render_template("index.html")


# RUTAS DEL FRONTEND
@app.route('/biblioteca')
def biblioteca():
    return render_template('biblioteca.html')


@app.route('/galeria')
def galeria():
    return render_template('galeria.html')


@app.route('/mapa')
def mapa():
    return render_template('mapa.html')


@app.route('/crear')
def crear():
    return render_template('crear.html')


@app.route('/crear-documento')
def crear_documento():
    return render_template('crear_documento.html')


@app.route('/crear-imagen')
def crear_imagen():
    return render_template('crear_imagen.html')


@app.route('/crear-local')
def crear_local():
    return render_template('crear_local.html')


# CONEXIÓN A LA BASE DE DATOS
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