from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, jsonify, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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


# PÁGINA PRINCIPAL
@app.route("/")
def index():
    return render_template("index.html")


# RUTAS DEL FRONTEND
UPLOAD_FOLDER = 'static/assets/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


UPLOAD_FOLDER_DOC = 'static/assets/docs'
ALLOWED_EXTENSIONS_DOC = {'pdf'}
app.config['UPLOAD_FOLDER_DOC'] = UPLOAD_FOLDER_DOC

def allowed_file_documento(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_DOC

########################################################################
#BIBLIOTECA
@app.route('/biblioteca')
def biblioteca():
    archivos = obtener_archivos_biblioteca()
    return render_template('biblioteca.html', libritos=archivos)

#AGREGAR UN NUEVO DOCUMENTO
@app.route('/crear-documento', methods=['GET', 'POST'])
def crear_documento():
    if request.method == 'GET':
        categorias = mostrar_categorias()
        return render_template('crear_documento.html', categ=categorias)
    elif request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        file = request.files.get('URL')
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria')
        propietario_id = request.form.get('propietario_id')
        estado = 'activo'
        fecha_creacion = datetime.now()
        fecha_modificacion = datetime.now()
 
        #VALIDACIONES
        erroresD =[]
        if not nombre or len(nombre) > 100:
            erroresD.append("El nombre es obligatorio y no debe exceder los 100 caracteres.")
        if not descripcion or len(descripcion) > 500:
            erroresD.append("La descripción es obligatoria y no debe exceder los 500 caracteres.")
        if not tipo: 
            erroresD.append("El tipo de archivo es obligatorio.")
        if not categoria:
            erroresD.append("Debe seleccionar una categoría.")
        if  not file or not allowed_file_documento(file.filename):
            erroresD.append("El archivo es obligatorio y debe ser un tipo permitido PDF.")   
 
        if erroresD:
            categorias = mostrar_categorias()
            return render_template('crear_documento.html', erroresD=erroresD, categ=categorias)
 
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER_DOC'], filename)
        file.save(filepath)
        URLfile = f"{app.config['UPLOAD_FOLDER_DOC']}/{filename}"
 
        print(nombre, descripcion, URLfile, categoria, tipo, fecha_creacion, fecha_modificacion, propietario_id, estado)
        insertar_archivo(
            nombre,
            descripcion,
            URLfile,
            categoria,
            tipo,
            fecha_creacion,
            fecha_modificacion,
            propietario_id,
            estado
        )
        return redirect('/biblioteca')
            
    return render_template('crear_documento.html')

#EDITAR DOCUMENTO
@app.route('/documentos/editar/<int:id_archivo>', methods=["GET", "POST"])
def editar_documento(id_archivo):
    if request.method == "POST":
        archivo = obtener_un_archivo(id_archivo)
        # archivo: (id_archivo, nombre, descripcion, URL, categoria_id, tipo,
        #           fecha_creacion, fecha_modificacion, administrador_id, estado)
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria')
        estado = request.form.get('estado', 'activo')
        file = request.files.get('URL')
 
        #VALIDACIONES
        erroresD = []
        if not nombre or len(nombre) > 100:
            erroresD.append("El nombre es obligatorio y no debe exceder los 100 caracteres.")
        if not descripcion or len(descripcion) > 500:
            erroresD.append("La descripción es obligatoria y no debe exceder los 500 caracteres.")
        if not tipo:
            erroresD.append("El tipo de archivo es obligatorio.")
        if not categoria:
            erroresD.append("Debe seleccionar una categoría.")
        if file and file.filename and not allowed_file_documento(file.filename):
            erroresD.append("El archivo debe ser un tipo permitido PDF.")
 
        if erroresD:
            categorias = mostrar_categorias()
            return render_template("editar_documento.html", archivo=archivo, categ=categorias, erroresD=erroresD)
 
        # Si no suben un archivo nuevo, se mantiene la URL que ya tenía
        if file and file.filename and allowed_file_documento(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER_DOC'], filename)
            file.save(filepath)
            URLfile = f"{app.config['UPLOAD_FOLDER_DOC']}/{filename}"
        else:
            URLfile = archivo[3]
 
        fecha_modificacion = datetime.now()
        administrador_id = archivo[8]  # se mantiene el mismo, hasta que haya login
 
        actualizar_archivo(
            id_archivo,
            nombre,
            descripcion,
            URLfile,
            categoria,
            tipo,
            fecha_modificacion,
            administrador_id,
            estado
        )
        return redirect('/biblioteca')
    else:
        archivo = obtener_un_archivo(id_archivo)
        categorias = mostrar_categorias()
        return render_template("editar_documento.html", archivo=archivo, categ=categorias)

#BUSCAR DOCUMENTO
@app.route('/buscar_documento')
def buscar_documento():
    q = request.args.get('q', '')
    archivos = []
    if q:
        resultados = obtener_archivos_por_nombre(q)
        archivos = [
            {
                'id': row[0],
                'nombre': row[1],
                'descripcion': row[2],
                'URL': row[3],
                'categoria_id': row[4],
                'tipo': row[5],
                'estado': row[9]
            }
            for row in resultados
        ]
    return jsonify(archivos)

########################################################################
#GALERIA
@app.route('/galeria')
def galeria():
    imagenes = obtener_imagenes()
    return render_template('galeria.html')

#AGREGAR IMAGEN 
@app.route('/crear-imagen', methods=['GET', 'POST'])
def crear_imagen():
   if request.method == 'GET':
          categorias = mostrar_categorias()
          return render_template('crear_imagen.html', cat=categorias)
   elif request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        file = request.files.get('URL')
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria')
        propietario_id = request.form.get('propietario_id')
        estado = 'activo'
        fecha_creacion = datetime.now()
        fecha_modificacion = datetime.now()
     
        #VALIDACIONES
        erroresD =[]
        if not nombre or len(nombre) > 100:
            erroresD.append("El nombre es obligatorio y no debe exceder los 100 caracteres.")
        if not descripcion or len(descripcion) > 500:
            erroresD.append("La descripción es obligatoria y no debe exceder los 500 caracteres.")
        if not tipo: 
            erroresD.append("El tipo de archivo es obligatorio.")
        if not categoria:
            erroresD.append("Debe seleccionar una categoría.")
        if  not file or not allowed_file_documento(file.filename):
            erroresD.append("El archivo es obligatorio y debe ser un tipo permitido PDF.")   
     
        if erroresD:
            categorias = mostrar_categorias()
            return render_template('crear_imagen.html', erroresD=erroresD, categ=categorias)
     
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER_DOC'], filename)
        file.save(filepath)
        URLfile = f"{app.config['UPLOAD_FOLDER_DOC']}/{filename}"
     
        print(nombre, descripcion, URLfile, categoria, tipo, fecha_creacion, fecha_modificacion, propietario_id, estado)
        insertar_archivo(
            nombre,
            descripcion,
            URLfile,
            categoria,
            tipo,
            fecha_creacion,
            fecha_modificacion,
            propietario_id,
            estado
            )
        return redirect('/galeria')

       
   return render_template('crear_imagen.html')

#EDITAR IMAGEN
@app.route('/galeria/editar/<int:id_archivo>', methods=["GET", "POST"])
def editar_imagen(id_archivo):
    if request.method == "POST":
        archivo = obtener_un_archivo(id_archivo)
        # archivo: (id_archivo, nombre, descripcion, URL, categoria_id, tipo,
        #           fecha_creacion, fecha_modificacion, administrador_id, estado)
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria')
        estado = request.form.get('estado', 'activo')
        file = request.files.get('URL')
 
        #VALIDACIONES
        erroresD = []
        if not nombre or len(nombre) > 100:
            erroresD.append("El nombre es obligatorio y no debe exceder los 100 caracteres.")
        if not descripcion or len(descripcion) > 500:
            erroresD.append("La descripción es obligatoria y no debe exceder los 500 caracteres.")
        if not tipo:
            erroresD.append("El tipo de archivo es obligatorio.")
        if not categoria:
            erroresD.append("Debe seleccionar una categoría.")
        if file and file.filename and not allowed_file_documento(file.filename):
            erroresD.append("El archivo debe ser un tipo permitido PDF.")
 
        if erroresD:
            categorias = mostrar_categorias()
            return render_template("editar_imagen.html", archivo=archivo, categ=categorias, erroresD=erroresD)
 
        # Si no suben un archivo nuevo, se mantiene la URL que ya tenía
        if file and file.filename and allowed_file_documento(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER_DOC'], filename)
            file.save(filepath)
            URLfile = f"{app.config['UPLOAD_FOLDER_DOC']}/{filename}"
        else:
            URLfile = archivo[3]
 
        fecha_modificacion = datetime.now()
        administrador_id = archivo[8]  # se mantiene el mismo, hasta que haya login
 
        actualizar_archivo(
            id_archivo,
            nombre,
            descripcion,
            URLfile,
            categoria,
            tipo,
            fecha_modificacion,
            administrador_id,
            estado
        )
        return redirect('/galeria')
    else:
        archivo = obtener_un_archivo(id_archivo)
        categorias = mostrar_categorias()
        return render_template("editar_imagen.html", archivo=archivo, categ=categorias)

#BUSCAR IMAGEN
@app.route('/buscar_imagen')
def buscar_imagen():
    q = request.args.get('q', '')
    imagenes = []
    if q:
        resultados = obtener_archivos_por_nombre(q)
        imagenes = [
            {
                'id': row[0],
                'nombre': row[1],
                'descripcion': row[2],
                'URL': row[3],
                'categoria_id': row[4],
                'tipo': row[5],
                'estado': row[9]
            }
            for row in resultados
        ]
    return jsonify(imagenes)

##############################################################################
#MAPA
@app.route('/mapa')
def mapa():
    return render_template('mapa.html')

@app.route('/crear-local')
def crear_local():
    return render_template('crear_local.html')

#############################################################################
#JUEGOS
@app.route('/crear')
def crear():
    return render_template('crear.html')


#############################################################################
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