from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy 
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app) 

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/biblioteca')
def biblioteca():
    return render_template('biblioteca.html')

@app.route('/galeria')
def galeria():
    # Si aún no tenés galeria.html, podés dejar un texto temporal
    # o crear el archivo base para que Flask no tire error
    return render_template('galeria.html')

@app.route('/mapa')
def mapa():
    return render_template('mapa.html')

@app.route('/crear')
def crear():
    return render_template('crear.html')

@app.route('/crear-documento')
def crear_documento():
    # Aquí en el futuro podés agregar lógica para verificar si el usuario es admin
    return render_template('crear_documento.html')

# Y ya que estamos, podés dejar preparada la de la galería para después:
@app.route('/crear-imagen')
def crear_imagen():
    return render_template('crear_imagen.html')

@app.route('/crear-local')
def crear_local():
    return render_template('crear_local.html')

from sqlalchemy import text

@app.route('/test-conexion')
def test_conexion():
    try:

        db.session.execute(text('SELECT 1'))
        return "Conexión a Supabase exitosa."
    except Exception as e:
        return f"Error en la conexión: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)