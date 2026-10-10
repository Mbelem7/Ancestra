from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy 
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine

app = Flask(__name__)

load_dotenv()


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

@app.route('/editar-documento')
def editar_documento():
    # Más adelante aquí podrán recibir el ID del documento, ej: /editar-documento/<int:id>
    return render_template('editar_documento.html')

@app.route('/editar-imagen')
def editar_imagen():
    return render_template('editar_imagen.html')

@app.route('/editar-local')
def editar_local():
    return render_template('editar_lugar.html')




if __name__ == "__main__":
    app.run(debug=True)

    
# from sqlalchemy.pool import NullPool


# 1. Obtener las variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# 2. Construir la URL de conexión de Supabase
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

# 3. Pasársela a la configuración de Flask
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 4. Inicializar la base de datos con tu app
db = SQLAlchemy(app)

# Test rápido para ver si conecta al arrancar Flask (opcional, equivalente a tu bloque try/except)
with app.app_context():
    try:
        db.engine.connect()
        print("¡Conexión a Supabase exitosa, rey!")
    except Exception as e:
        print(f"Error al conectar a Supabase: {e}")


class Lugar(db.Model):
    # Asegurate de que el nombre coincida con tu tabla (LUGAR en mayúscula según la imagen)
    __tablename__ = 'LUGAR' 
    
    id_lugar = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String, nullable=True)
    descripcion = db.Column(db.String, nullable=True)
    direccion = db.Column(db.String, nullable=True)
    contacto = db.Column(db.Integer, nullable=True)
    
    # Manejo de fechas automáticas delegadas a PostgreSQL
    fecha_creacion = db.Column(db.DateTime, server_default=db.func.now())
    
    # Fíjate cómo vinculamos la variable de Python con la columna que tiene espacios en Supabase
    fecha_modificacion = db.Column('fecha modificacion', db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    administrador_id = None

    def __repr__(self):
        return f'<Lugar {self.nombre}>'

@app.route('/test-db')
def test_db():
    # Creamos un nuevo objeto usando los campos exactos de tu tabla
    nuevo_lugar = Lugar(
        nombre="Plaza de Magdalena",
        descripcion="Barrio histórico de la comunidad de Monimbó.",
        direccion="De la iglesia San Jerónimo 2c al sur",
        contacto=88888888,
        administrador_id=1  # Suponiendo que el admin con ID 1 existe
    )
    
    try:
        db.session.add(nuevo_lugar)
        db.session.commit()
        return "¡Lugar guardado con éxito en Supabase, rey! Andá a revisar la tabla LUGAR."
    except Exception as e:
        db.session.rollback()
        return f"Falló el guardado: {e}"