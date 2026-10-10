from datetime import datetime, date
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, jsonify, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os


app = Flask(__name__)
 
load_dotenv()
########################################################################
#LOGIN
app.secret_key = os.getenv("SECRET_KEY")
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

########################################################################
#BASE DE DATOS
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

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,   # antes de usar una conexión, comprueba que siga viva y la reconecta si no
    'pool_recycle': 280,     # renueva las conexiones cada ~5 minutos
}

# 4. Inicializar la base de datos con tu app
db = SQLAlchemy(app)

# Test rápido para ver si conecta al arrancar Flask (opcional, equivalente a tu bloque try/except)
with app.app_context():
    try:
        db.engine.connect()
        print("¡Conexión a Supabase exitosa, rey!")
    except Exception as e:
        print(f"Error al conectar a Supabase: {e}")

########################################################################
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
from modulos.administrador import *
import random
import string
import re
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

########################################################################
#LOGICA DEL LOGIN Y REGISTRO
#LOGIN Y PERMISOS
CORREO_VALIDO = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

AVISOS_LOGIN = {
    'docente_pendiente': 'Tu cuenta de docente fue creada. Un administrador debe aprobarla antes de que puedas crear plantillas. Ya puedes iniciar sesión.'
}


def redirigir_a_login():
    # Si lo pidió el juego (fetch con JSON) se responde con JSON; si no, se manda a la pantalla de login
    if request.is_json:
        return jsonify({'error': 'Debes iniciar sesión'}), 401
    if request.method == 'GET':
        return redirect(url_for('login', next=request.full_path.rstrip('?')))
    return redirect(url_for('login'))


def destino_seguro(destino):
    # Solo se acepta una ruta de este mismo sitio (evita mandar al usuario a una página de afuera)
    if destino and destino.startswith('/') and not destino.startswith('//') and not destino.startswith('/\\'):
        return destino
    return None


def iniciar_sesion(persona_id, nombre_1, apellido_1, tipo, rol_id):
    session.clear()
    session['persona_id'] = persona_id
    session['nombre'] = f"{nombre_1} {apellido_1}"
    session['tipo'] = tipo          # 'estudiante', 'docente' o 'administrador'
    session['rol_id'] = rol_id      # id_estudiante, id_docente o id_administrador


def id_del_rol(persona_id, tipo):
    # Busca el perfil (docente, estudiante o administrador) que corresponde a la persona
    if tipo == 'docente':
        perfil = obtener_docente_por_persona(persona_id)
    elif tipo == 'estudiante':
        perfil = obtener_estudiante_por_persona(persona_id)
    elif tipo == 'administrador':
        perfil = obtener_administrador_por_persona(persona_id)
    else:
        perfil = None
    return perfil[0] if perfil else None


def ids_de_creador():
    # (docente_id, administrador_id) de quien está creando algo
    if session.get('tipo') == 'docente':
        return session.get('rol_id'), None
    if session.get('tipo') == 'administrador':
        return None, session.get('rol_id')
    return None, None


def login_required(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        if 'persona_id' not in session:
            return redirigir_a_login()
        return f(*args, **kwargs)
    return envoltura


def rol_requerido(*roles):
    def decorador(f):
        @wraps(f)
        def envoltura(*args, **kwargs):
            if 'persona_id' not in session:
                return redirigir_a_login()
            if session.get('tipo') not in roles:
                return render_template('acceso_denegado.html'), 403
            return f(*args, **kwargs)
        return envoltura
    return decorador


def puede_crear_plantillas(f):
    # Administradores sí; docentes solo si un administrador ya los aprobó (se revisa en la base cada vez)
    @wraps(f)
    def envoltura(*args, **kwargs):
        if 'persona_id' not in session:
            return redirigir_a_login()
        tipo = session.get('tipo')
        if tipo == 'administrador':
            return f(*args, **kwargs)
        if tipo == 'docente':
            docente = obtener_docente_por_persona(session['persona_id'])
            if docente and docente[1] == 'verificado':
                return f(*args, **kwargs)
            return render_template('cuenta_pendiente.html', estado=docente[1] if docente else None), 403
        return render_template('acceso_denegado.html'), 403
    return envoltura

########################################################################
#REGISTRO
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'GET':
        return render_template('registro.html', datos={})

    tipo = request.form.get('tipo', '')
    nombre_1 = request.form.get('nombre_1', '').strip()
    nombre_2 = request.form.get('nombre_2', '').strip()
    apellido_1 = request.form.get('apellido_1', '').strip()
    apellido_2 = request.form.get('apellido_2', '').strip()
    fecha_texto = request.form.get('fecha_nacimiento', '').strip()
    correo = request.form.get('correo', '').strip().lower()
    contrasena = request.form.get('contrasena', '')
    confirmar = request.form.get('confirmar', '')

    #VALIDACIONES
    erroresR = []
    if tipo not in ('estudiante', 'docente'):
        erroresR.append("Elige si eres estudiante o docente.")
    if not nombre_1 or len(nombre_1) > 50:
        erroresR.append("El primer nombre es obligatorio y no debe exceder los 50 caracteres.")
    if len(nombre_2) > 50:
        erroresR.append("El segundo nombre no debe exceder los 50 caracteres.")
    if not apellido_1 or len(apellido_1) > 50:
        erroresR.append("El primer apellido es obligatorio y no debe exceder los 50 caracteres.")
    if len(apellido_2) > 50:
        erroresR.append("El segundo apellido no debe exceder los 50 caracteres.")

    fecha_nacimiento = None
    try:
        fecha_nacimiento = datetime.strptime(fecha_texto, '%Y-%m-%d').date()
        if fecha_nacimiento >= date.today() or fecha_nacimiento.year < 1900:
            raise ValueError
    except ValueError:
        erroresR.append("Escribe una fecha de nacimiento válida.")

    if not CORREO_VALIDO.match(correo) or len(correo) > 100:
        erroresR.append("Escribe un correo válido.")
    elif obtener_persona_por_correo(correo):
        erroresR.append("Ya existe una cuenta con ese correo.")

    if len(contrasena) < 8:
        erroresR.append("La contraseña debe tener al menos 8 caracteres.")
    elif contrasena != confirmar:
        erroresR.append("Las contraseñas no coinciden.")

    if erroresR:
        return render_template('registro.html', erroresR=erroresR, datos=request.form)

    ahora = datetime.now()
    id_persona = insertar_persona(
        nombre_1, nombre_2 or None, apellido_1, apellido_2 or None,
        fecha_nacimiento, correo, tipo, 'activo',
        generate_password_hash(contrasena), ahora, ahora
    )

    # Si falla la creación del perfil, se deshace la persona para no dejar una cuenta a medias
    try:
        if tipo == 'docente':
            insertar_docente(id_persona, 'pendiente')
        else:
            id_estudiante = insertar_estudiante(id_persona, 'activo')
    except Exception as error:
        print("No se pudo crear el perfil:", error)
        db.session.rollback()
        eliminar_persona(id_persona)
        return render_template('registro.html', erroresR=["No se pudo crear tu cuenta. Intenta de nuevo."], datos=request.form)

    if tipo == 'docente':
        return redirect(url_for('login', aviso='docente_pendiente'))

    iniciar_sesion(id_persona, nombre_1, apellido_1, 'estudiante', id_estudiante)
    return redirect(url_for('index'))

########################################################################
#LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    siguiente = request.args.get('next') or request.form.get('next') or ''

    if request.method == 'GET':
        return render_template('login.html', aviso=AVISOS_LOGIN.get(request.args.get('aviso')), siguiente=siguiente)

    correo = request.form.get('correo', '').strip().lower()
    contrasena = request.form.get('contrasena', '')

    persona = obtener_persona_por_correo(correo)
    # persona: (id_persona, nombre_1, apellido_1, correo, tipo, estado, contraseña)

    # El mismo mensaje si el correo no existe o la contraseña está mal, para no dar pistas
    if not persona or not persona[6] or not check_password_hash(persona[6], contrasena):
        return render_template('login.html', error="Correo o contraseña incorrectos.", siguiente=siguiente, correo=correo)

    if persona[5] != 'activo':
        return render_template('login.html', error="Tu cuenta está desactivada. Habla con un administrador.", siguiente=siguiente, correo=correo)

    rol_id = id_del_rol(persona[0], persona[4])
    if rol_id is None:
        return render_template('login.html', error="Tu cuenta no tiene un perfil asignado. Habla con un administrador.", siguiente=siguiente, correo=correo)

    iniciar_sesion(persona[0], persona[1], persona[2], persona[4], rol_id)
    return redirect(destino_seguro(siguiente) or url_for('index'))


#LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


#ADMIN - APROBAR DOCENTES
@app.route('/admin/docentes')
@rol_requerido('administrador')
def admin_docentes():
    docentes = obtener_docentes()
    # d: (id_docente, estado_verificacion, id_persona, nombre_1, nombre_2, apellido_1, apellido_2,
    #     fecha_nacimiento, correo, estado)
    orden = {'pendiente': 0, 'rechazado': 1, 'verificado': 2}
    docentes = sorted(docentes, key=lambda d: orden.get(d[1], 3))
    return render_template('admin_docentes.html', docentes=docentes)


@app.route('/admin/docentes/<int:id_docente>/estado', methods=['POST'])
@rol_requerido('administrador')
def admin_docente_estado(id_docente):
    nuevo_estado = request.form.get('estado')
    if nuevo_estado in ('pendiente', 'verificado', 'rechazado') and obtener_un_docente(id_docente):
        actualizar_estado_verificacion(id_docente, nuevo_estado)
    return redirect(url_for('admin_docentes'))

########################################################################
# PÁGINA PRINCIPAL
@app.route("/")
def index():
    return render_template("index.html")

########################################################################
# RUTAS DE APOYO Y FUNCIONES AUXILIARES
#ARCHIVOS Y URLS
#IMAGENES
UPLOAD_FOLDER = 'static/assets/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg', 'mp4', 'webm'}
app.config['UPLOAD_FOLDER_IMG'] = UPLOAD_FOLDER
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#DOCUMENTOS
UPLOAD_FOLDER_DOC = 'static/assets/docs'
ALLOWED_EXTENSIONS_DOC = {'pdf'}
app.config['UPLOAD_FOLDER_DOCS'] = UPLOAD_FOLDER_DOC

def allowed_file_documento(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_DOC

#CODIGO DE ACCESO PARA LOS JUEGOS
def generar_codigo_acceso():
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not obtener_plantilla_por_codigo(codigo):
            return codigo

#COORDENADAS DEL MAPA
def coordenadas_validas(latitud, longitud):
    try:
        lat = float(latitud)
        lng = float(longitud)
    except (TypeError, ValueError):
        return False
    return -90 <= lat <= 90 and -180 <= lng <= 180

#PREGUNTAS DE PLANTILLAS
def indices_de_preguntas():
    # Números de las preguntas que llegaron en el formulario.
    # Si el docente eliminó alguna, faltan números (ej: 1 y 3), por eso no se cuenta de 1 en 1.
    numeros = []
    for campo in request.form:
        encontrado = re.fullmatch(r'pregunta_(\d+)_enunciado', campo)
        if encontrado:
            numeros.append(int(encontrado.group(1)))
    return sorted(numeros)
 
########################################################################
#BIBLIOTECA
@app.route('/biblioteca')
def biblioteca():
    archivos = obtener_archivos_biblioteca()
    return render_template('biblioteca.html', libritos=archivos)
 
#AGREGAR UN NUEVO DOCUMENTO
@app.route('/crear-documento', methods=['GET', 'POST'])
@rol_requerido('administrador')
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
        propietario_id = session.get('rol_id')
        estado = 'activo'
        fecha_creacion = datetime.now()
        fecha_modificacion = datetime.now()
 
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
        if not file or not allowed_file_documento(file.filename):
            erroresD.append("El archivo es obligatorio y debe ser un tipo permitido PDF.")
 
        if erroresD:
            categorias = mostrar_categorias()
            return render_template('crear_documento.html', erroresD=erroresD, categ=categorias)
 
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename)
        file.save(filepath)
        URLfile = f"{app.config['UPLOAD_FOLDER_DOCS']}/{filename}"
 
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
@rol_requerido('administrador')
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
            filepath = os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename)
            file.save(filepath)
            URLfile = f"{app.config['UPLOAD_FOLDER_DOCS']}/{filename}"
        else:
            URLfile = archivo[3]
 
        fecha_modificacion = datetime.now()
        administrador_id = archivo[8] or session.get('rol_id') 
 
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
    imagenes = obtener_archivos_galeria()
    categorias = mostrar_categorias()
    return render_template('galeria.html', imag=imagenes, categ=categorias)
 
#AGREGAR IMAGEN
@app.route('/crear-imagen', methods=['GET', 'POST'])
@rol_requerido('administrador')
def crear_imagen():
    if request.method == 'GET':
        categorias = mostrar_categorias()
        return render_template('crear_imagen.html', categ=categorias)
    elif request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        file = request.files.get('URL')
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria')
        propietario_id = session.get('rol_id')
        estado = 'activo'
        fecha_creacion = datetime.now()
        fecha_modificacion = datetime.now()
 
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
        if not file or not allowed_file(file.filename):
            erroresD.append("El archivo es obligatorio y debe ser PNG, JPG, SVG, MP4 o WEBM.")
 
        if erroresD:
            categorias = mostrar_categorias()
            return render_template('crear_imagen.html', erroresD=erroresD, categ=categorias)
 
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER_IMG'], filename)
        file.save(filepath)
        URLfile = f"{app.config['UPLOAD_FOLDER_IMG']}/{filename}"
 
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
@rol_requerido('administrador')
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
        if file and file.filename and not allowed_file(file.filename):
            erroresD.append("El archivo es obligatorio y debe ser PNG, JPG, SVG, MP4 o WEBM.")
 
        if erroresD:
            categorias = mostrar_categorias()
            return render_template("editar_imagen.html", archivo=archivo, categ=categorias, erroresD=erroresD)
 
        # Si no suben un archivo nuevo, se mantiene la URL que ya tenía
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER_IMG'], filename)
            file.save(filepath)
            URLfile = f"{app.config['UPLOAD_FOLDER_IMG']}/{filename}"
        else:
            URLfile = archivo[3]
 
        fecha_modificacion = datetime.now()
        administrador_id = archivo[8] or session.get('rol_id')
 
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
    lugares = obtener_lugares()
    puntos = [
        {
            'nombre': l[1],
            'descripcion': l[2],
            'direccion': l[3],
            'contacto': l[8],
            'lat': float(l[9]),
            'lng': float(l[10]),
            'editar': url_for('editar_lugar', id_lugar=l[0])
        }
        for l in lugares if l[9] is not None and l[10] is not None
    ]
    return render_template('mapa.html', puntos=puntos)

#CREAR LUGAR
@app.route('/crear-local', methods=['GET', 'POST'])
@rol_requerido('administrador')
def crear_local():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        direccion = request.form.get('direccion')
        fecha_creacion = datetime.now()
        fecha_modificacion = datetime.now()
        administrador_id = session.get('rol_id')
        estado = 'activo'
        contacto = request.form.get('contacto')
        latitud = request.form.get('latitud')
        longitud = request.form.get('longitud')
 
        #VALIDACIONES
        erroresL = []
        if not nombre or len(nombre) > 100:
            erroresL.append("El nombre es obligatorio y no debe exceder los 100 caracteres.")
        if not descripcion or len(descripcion) > 500:
            erroresL.append("La descripción es obligatoria y no debe exceder los 500 caracteres.")
        if not direccion or len(direccion) > 200:
            erroresL.append("La dirección es obligatoria y no debe exceder los 200 caracteres.")
        if not contacto or not contacto.isdigit():
            erroresL.append("El contacto es obligatorio y debe ser un número de teléfono válido.")
        if not coordenadas_validas(latitud, longitud):
            erroresL.append("Debes marcar la ubicación del local en el mapa.")
 
        if erroresL:
            return render_template('crear_local.html', erroresL=erroresL)
 
        print(nombre, descripcion, direccion, fecha_creacion, fecha_modificacion, administrador_id, estado, contacto)
        insertar_lugar(
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
        return redirect('/mapa')
 
    return render_template('crear_local.html')
 
#EDITAR LUGAR
@app.route('/editar-lugar/<int:id_lugar>', methods=["GET", "POST"])
@rol_requerido('administrador')
def editar_lugar(id_lugar):
    if request.method == "POST":
        lugar = obtener_un_lugar(id_lugar)
        # lugar: (id_lugar, nombre, descripcion, direccion, fecha_creacion,
        #         fecha_modificacion, administrador_id, estado, contacto, latitud, longitud)
 
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        direccion = request.form.get('direccion')
        contacto = request.form.get('contacto')
        estado = request.form.get('estado', 'activo')
        latitud = request.form.get('latitud')
        longitud = request.form.get('longitud')
 
        #VALIDACIONES
        erroresL = []
        if not nombre or len(nombre) > 100:
            erroresL.append("El nombre es obligatorio y no debe exceder los 100 caracteres.")
        if not descripcion or len(descripcion) > 500:
            erroresL.append("La descripción es obligatoria y no debe exceder los 500 caracteres.")
        if not direccion or len(direccion) > 200:
            erroresL.append("La dirección es obligatoria y no debe exceder los 200 caracteres.")
        if not contacto or not contacto.isdigit():
            erroresL.append("El contacto es obligatorio y debe ser un número de teléfono válido.")
        if not coordenadas_validas(latitud, longitud):
            erroresL.append("Debes marcar la ubicación del local en el mapa.")
 
        if erroresL:
            return render_template("editar_lugar.html", lugar=lugar, erroresL=erroresL)
 
        fecha_modificacion = datetime.now()
        administrador_id = lugar[6] or session.get('rol_id')
 
        actualizar_lugar(
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
        )
        return redirect('/mapa')
    else:
        lugar = obtener_un_lugar(id_lugar)
        return render_template("editar_lugar.html", lugar=lugar)
 
#BUSCAR LUGAR
@app.route('/buscar_lugar')
def buscar_lugar():
    q = request.args.get('q', '')
    lugares = []
    if q:
        resultados = obtener_lugares_por_nombre(q)
        lugares = [
            {
                'id': row[0],
                'nombre': row[1],
                'descripcion': row[2],
                'direccion': row[3],
                'estado': row[7],
                'contacto': row[8]
            }
            for row in resultados
        ]
    return jsonify(lugares)

#############################################################################
#PLANTILLAS 
@app.route('/crear')
@puede_crear_plantillas
def crear():
    return render_template('crear.html')
 
#JUEGOS - VERDADERO Y FALSO
@app.route('/juegos/verdadero-falso/crear', methods=['GET', 'POST'])
@puede_crear_plantillas
def crear_vf():
    if request.method == 'GET':
        return render_template('juegos/crearvf.html')
 
    elif request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        docente_id, administrador_id = ids_de_creador()
        fecha_creacion = datetime.now()
        fecha_modificacion = datetime.now()
 
        #VALIDACIONES
        erroresP = []
        if not nombre or len(nombre) > 100:
            erroresP.append("El nombre es obligatorio y no debe exceder los 100 caracteres.")
        if not descripcion or len(descripcion) > 500:
            erroresP.append("La descripción es obligatoria y no debe exceder los 500 caracteres.")
 
        preguntas = []
        for i in indices_de_preguntas():
            enunciado = request.form.get(f'pregunta_{i}_enunciado')
            correcta = request.form.get(f'correcta_pregunta_{i}')
 
            if not enunciado:
                erroresP.append(f"La pregunta {i} no puede estar vacía.")
 
            respuestas = []
            j = 1
            while request.form.get(f'pregunta_{i}_respuesta_{j}') is not None:
                respuestas.append(request.form.get(f'pregunta_{i}_respuesta_{j}'))
                j += 1
 
            if len(respuestas) < 2:
                erroresP.append(f"La pregunta {i} necesita al menos 2 respuestas.")
            if not correcta or not correcta.isdigit() or int(correcta) > len(respuestas) or int(correcta) < 1:
                erroresP.append(f"Falta marcar la respuesta verdadera en la pregunta {i}.")
 
            preguntas.append({
                'enunciado': enunciado,
                'respuestas': respuestas,
                'correcta': int(correcta) if correcta and correcta.isdigit() else None
            })
 
        if len(preguntas) == 0:
            erroresP.append("La plantilla necesita al menos una pregunta.")
 
        if erroresP:
            return render_template('juegos/crearvf.html', erroresP=erroresP)
 
        id_juego = insertar_juego(
            nombre, descripcion, 'verdadero_falso',
            fecha_creacion, fecha_modificacion,
            administrador_id, 'activo'
        )
        codigo_acceso = generar_codigo_acceso()
        id_plantilla = insertar_plantilla(
            codigo_acceso, fecha_creacion, fecha_modificacion,
            id_juego, docente_id, administrador_id
        )
 
        for pregunta in preguntas:
            id_pregunta = insertar_pregunta(
                pregunta['enunciado'], fecha_creacion, fecha_modificacion,
                id_plantilla, id_juego, administrador_id
            )
            for indice, texto in enumerate(pregunta['respuestas'], start=1):
                tipo = 'correcta' if indice == pregunta['correcta'] else 'incorrecta'
                insertar_respuesta(
                    texto, tipo, fecha_creacion, fecha_modificacion,
                    id_pregunta, id_juego, administrador_id
                )
 
        return render_template('juegos/plantilla_creada.html',
                                nombre=nombre, codigo_acceso=codigo_acceso)
 
 
############################
#JUEGOS - SELECCIÓN MÚLTIPLE
@app.route('/juegos/multiple/crear', methods=['GET', 'POST'])
@puede_crear_plantillas
def crear_multiple():
    if request.method == 'GET':
        return render_template('juegos/crearmult.html')
 
    elif request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        docente_id, administrador_id = ids_de_creador()
        fecha_creacion = datetime.now()
        fecha_modificacion = datetime.now()
 
        #VALIDACIONES
        erroresP = []
        if not nombre or len(nombre) > 100:
            erroresP.append("El nombre es obligatorio y no debe exceder los 100 caracteres.")
        if not descripcion or len(descripcion) > 500:
            erroresP.append("La descripción es obligatoria y no debe exceder los 500 caracteres.")
 
        preguntas = []
        for i in indices_de_preguntas():
            enunciado = request.form.get(f'pregunta_{i}_enunciado')
            correcta = request.form.get(f'correcta_pregunta_{i}')
 
            if not enunciado:
                erroresP.append(f"La pregunta {i} no puede estar vacía.")
 
            respuestas = []
            j = 1
            while request.form.get(f'pregunta_{i}_respuesta_{j}') is not None:
                respuestas.append(request.form.get(f'pregunta_{i}_respuesta_{j}'))
                j += 1
 
            if len(respuestas) < 2:
                erroresP.append(f"La pregunta {i} necesita al menos 2 opciones.")
            if not correcta or not correcta.isdigit() or int(correcta) > len(respuestas) or int(correcta) < 1:
                erroresP.append(f"Falta marcar la opción correcta en la pregunta {i}.")
 
            preguntas.append({
                'enunciado': enunciado,
                'respuestas': respuestas,
                'correcta': int(correcta) if correcta and correcta.isdigit() else None
            })
 
        if len(preguntas) == 0:
            erroresP.append("La plantilla necesita al menos una pregunta.")
 
        if erroresP:
            return render_template('juegos/crearmult.html', erroresP=erroresP)
 
        id_juego = insertar_juego(
            nombre, descripcion, 'seleccion_multiple',
            fecha_creacion, fecha_modificacion,
            administrador_id, 'activo'
        )
        codigo_acceso = generar_codigo_acceso()
        id_plantilla = insertar_plantilla(
            codigo_acceso, fecha_creacion, fecha_modificacion,
            id_juego, docente_id, administrador_id
        )
 
        for pregunta in preguntas:
            id_pregunta = insertar_pregunta(
                pregunta['enunciado'], fecha_creacion, fecha_modificacion,
                id_plantilla, id_juego, administrador_id
            )
            for indice, texto in enumerate(pregunta['respuestas'], start=1):
                tipo = 'correcta' if indice == pregunta['correcta'] else 'incorrecta'
                insertar_respuesta(
                    texto, tipo, fecha_creacion, fecha_modificacion,
                    id_pregunta, id_juego, administrador_id
                )
 
        return render_template('juegos/plantilla_creada.html',
                                nombre=nombre, codigo_acceso=codigo_acceso)
 
 
####################
#JUEGOS - COMPLETAR
@app.route('/juegos/completar/crear', methods=['GET', 'POST'])
@puede_crear_plantillas
def crear_completar():
    if request.method == 'GET':
        return render_template('juegos/crearcomp.html')
 
    elif request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        docente_id, administrador_id = ids_de_creador()
        fecha_creacion = datetime.now()
        fecha_modificacion = datetime.now()
 
        #VALIDACIONES
        erroresP = []
        if not nombre or len(nombre) > 100:
            erroresP.append("El nombre es obligatorio y no debe exceder los 100 caracteres.")
        if not descripcion or len(descripcion) > 500:
            erroresP.append("La descripción es obligatoria y no debe exceder los 500 caracteres.")
 
        preguntas = []
        for i in indices_de_preguntas():
            enunciado = request.form.get(f'pregunta_{i}_enunciado')
            respuesta = request.form.get(f'pregunta_{i}_respuesta')
 
            if not enunciado:
                erroresP.append(f"La pregunta {i} no puede estar vacía.")
            if not respuesta:
                erroresP.append(f"Falta la respuesta correcta en la pregunta {i}.")
 
            preguntas.append({'enunciado': enunciado, 'respuesta': respuesta})
 
        if len(preguntas) == 0:
            erroresP.append("La plantilla necesita al menos una pregunta.")
 
        if erroresP:
            return render_template('juegos/crearcomp.html', erroresP=erroresP)
 
        id_juego = insertar_juego(
            nombre, descripcion, 'completar',
            fecha_creacion, fecha_modificacion,
            administrador_id, 'activo'
        )
        codigo_acceso = generar_codigo_acceso()
        id_plantilla = insertar_plantilla(
            codigo_acceso, fecha_creacion, fecha_modificacion,
            id_juego, docente_id, administrador_id
        )
 
        for pregunta in preguntas:
            id_pregunta = insertar_pregunta(
                pregunta['enunciado'], fecha_creacion, fecha_modificacion,
                id_plantilla, id_juego, administrador_id
            )
            insertar_respuesta(
                pregunta['respuesta'], 'correcta', fecha_creacion, fecha_modificacion,
                id_pregunta, id_juego, administrador_id
            )
 
        return render_template('juegos/plantilla_creada.html',
                                nombre=nombre, codigo_acceso=codigo_acceso)
 
 
#########################
#JUEGOS - UNIR CON LÍNEA
@app.route('/juegos/union/crear', methods=['GET', 'POST'])
@puede_crear_plantillas
def crear_union():
    if request.method == 'GET':
        return render_template('juegos/crearun.html')
 
    elif request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        docente_id, administrador_id = ids_de_creador()
        fecha_creacion = datetime.now()
        fecha_modificacion = datetime.now()
 
        #VALIDACIONES
        erroresP = []
        if not nombre or len(nombre) > 100:
            erroresP.append("El nombre es obligatorio y no debe exceder los 100 caracteres.")
        if not descripcion or len(descripcion) > 500:
            erroresP.append("La descripción es obligatoria y no debe exceder los 500 caracteres.")
 
        parejas = []
        for i in indices_de_preguntas():
            enunciado = request.form.get(f'pregunta_{i}_enunciado')
            respuesta = request.form.get(f'pregunta_{i}_respuesta')
 
            if not enunciado:
                erroresP.append(f"La pareja {i} no puede tener el elemento izquierdo vacío.")
            if not respuesta:
                erroresP.append(f"La pareja {i} no puede tener el elemento derecho vacío.")
 
            parejas.append({'enunciado': enunciado, 'respuesta': respuesta})
 
        if len(parejas) < 2:
            erroresP.append("La plantilla necesita al menos 2 parejas.")
 
        if erroresP:
            return render_template('juegos/crearun.html', erroresP=erroresP)
 
        id_juego = insertar_juego(
            nombre, descripcion, 'union',
            fecha_creacion, fecha_modificacion,
            administrador_id, 'activo'
        )
        codigo_acceso = generar_codigo_acceso()
        id_plantilla = insertar_plantilla(
            codigo_acceso, fecha_creacion, fecha_modificacion,
            id_juego, docente_id, administrador_id
        )
 
        for pareja in parejas:
            id_pregunta = insertar_pregunta(
                pareja['enunciado'], fecha_creacion, fecha_modificacion,
                id_plantilla, id_juego, administrador_id
            )
            insertar_respuesta(
                pareja['respuesta'], 'correcta', fecha_creacion, fecha_modificacion,
                id_pregunta, id_juego, administrador_id
            )
 
        return render_template('juegos/plantilla_creada.html',
                                nombre=nombre, codigo_acceso=codigo_acceso)
 
 #############################################################################
 
#MIS PLANTILLAS
@app.route('/mis-plantillas')
@puede_crear_plantillas
def mis_plantillas():
    docente_id, _ = ids_de_creador()   # el administrador no tiene docente_id, así que ve todas
    plantillas = obtener_plantillas_resumen(docente_id)
    return render_template('juegos/mis_plantillas.html', plantillas=plantillas)

#############################################################################
#JUGAR
TIEMPO_POR_PREGUNTA = 20      # segundos que tiene el estudiante para cada pregunta
PUNTOS_POR_PREGUNTA = 10      # puntos por cada respuesta correcta
JUEGOS_DISPONIBLES = ['verdadero_falso']   # a medida que se construyan los demás juegos, se agregan aquí
NOMBRES_TIPO = {
    'verdadero_falso': 'Verdadero y Falso',
    'seleccion_multiple': 'Selección múltiple',
    'completar': 'Completar',
    'union': 'Unir con línea'
}
 
 
def cargar_plantilla_activa(id_plantilla):
    # Devuelve (plantilla, juego) si la plantilla existe y su juego está activo; si no, None
    plantilla = obtener_una_plantilla(id_plantilla)
    # plantilla: (id_plantilla, codigo_acceso, fecha_creacion, fecha_modificacion,
    #             juego_id, docente_id, administrador_id)
    if not plantilla:
        return None
    juego = obtener_un_juego(plantilla[4])
    # juego: (id_juego, nombre, descripcion, tipo, fecha_creacion,
    #         fecha_modificacion, administrador_id, estado)
    if not juego or juego[7] != 'activo':
        return None
    return plantilla, juego
 
 
#PASO 1: el estudiante escribe el código de acceso
@app.route('/jugar', methods=['GET', 'POST'])
@login_required
def jugar():
    if request.method == 'GET':
        return render_template('juegos/jugar.html')
 
    codigo = request.form.get('codigo', '').upper().strip()
    plantilla = obtener_plantilla_por_codigo(codigo)
 
    if not plantilla:
        return render_template('juegos/jugar.html', error="Ese código no existe.")
    if not cargar_plantilla_activa(plantilla[0]):
        return render_template('juegos/jugar.html', error="Esta plantilla no está disponible.")
 
    return redirect(url_for('jugar_plantilla', id_plantilla=plantilla[0]))
 
 
#PASO 2: pantalla con la información del juego y el botón "Jugar"
@app.route('/jugar/<int:id_plantilla>')
@login_required
def jugar_plantilla(id_plantilla):
    datos = cargar_plantilla_activa(id_plantilla)
    if not datos:
        return render_template('juegos/jugar.html', error="Esta plantilla no está disponible.")
    plantilla, juego = datos
 
    preguntas = obtener_preguntas_por_plantilla(id_plantilla)
    return render_template(
        'juegos/plantilla_encontrada.html',
        juego=juego,
        id_plantilla=id_plantilla,
        total_preguntas=len(preguntas),
        tiempo=TIEMPO_POR_PREGUNTA,
        nombre_tipo=NOMBRES_TIPO.get(juego[3], juego[3]),
        disponible=(juego[3] in JUEGOS_DISPONIBLES and len(preguntas) > 0)
    )
 
 
#PASO 3: la partida (por ahora solo Verdadero y Falso)
@app.route('/jugar/<int:id_plantilla>/partida')
@login_required
def jugar_partida(id_plantilla):
    datos = cargar_plantilla_activa(id_plantilla)
    if not datos:
        return redirect(url_for('jugar'))
    plantilla, juego = datos
 
    if juego[3] not in JUEGOS_DISPONIBLES:
        return redirect(url_for('jugar_plantilla', id_plantilla=id_plantilla))
 
    # Al navegador se le mandan las preguntas y sus opciones, SIN decir cuál es la correcta
    preguntas = []
    for pregunta in sorted(obtener_preguntas_por_plantilla(id_plantilla), key=lambda p: p[0]):
        opciones = [
            {'id': r[0], 'texto': r[1]}
            for r in sorted(obtener_respuestas_por_pregunta(pregunta[0]), key=lambda r: r[0])
        ]
        preguntas.append({'id': pregunta[0], 'enunciado': pregunta[1], 'opciones': opciones})
 
    if not preguntas:
        return redirect(url_for('jugar_plantilla', id_plantilla=id_plantilla))
 
    return render_template(
        'juegos/jugar_vf.html',
        juego=juego,
        id_plantilla=id_plantilla,
        preguntas=preguntas,
        tiempo=TIEMPO_POR_PREGUNTA
    )
 
 
#PASO 4: el servidor califica lo que el estudiante respondió (y lo guarda si es estudiante)
@app.route('/jugar/<int:id_plantilla>/resultado', methods=['POST'])
@login_required
def jugar_resultado(id_plantilla):
    datos = cargar_plantilla_activa(id_plantilla)
    if not datos:
        return jsonify({'error': 'Plantilla no disponible'}), 404
    plantilla, juego = datos
 
    # elegidas: {"id_pregunta": id_respuesta, ...} (null si no alcanzó a responder)
    cuerpo = request.get_json(silent=True)
    elegidas = cuerpo.get('respuestas', {}) if isinstance(cuerpo, dict) else {}
    if not isinstance(elegidas, dict):
        elegidas = {}
 
    detalle = []
    por_guardar = []   # (id de la respuesta elegida o None, si acertó), una por pregunta
    aciertos = 0
    for pregunta in sorted(obtener_preguntas_por_plantilla(id_plantilla), key=lambda p: p[0]):
        respuestas = obtener_respuestas_por_pregunta(pregunta[0])
        # respuesta: (id_respuesta, respuesta, tipo, fecha_creacion, fecha_modificacion,
        #             pregunta_id, juego_id, administrador_id)
        correcta = next((r for r in respuestas if r[2] == 'correcta'), None)
 
        # Solo vale si la respuesta elegida pertenece a ESTA pregunta
        id_elegida = elegidas.get(str(pregunta[0]))
        elegida = next((r for r in respuestas if r[0] == id_elegida), None)
 
        acerto = elegida is not None and correcta is not None and elegida[0] == correcta[0]
        if acerto:
            aciertos += 1
 
        por_guardar.append((elegida[0] if elegida else None, acerto))
        detalle.append({
            'enunciado': pregunta[1],
            'tu_respuesta': elegida[1] if elegida else None,
            'correcta': correcta[1] if correcta else None,
            'acerto': acerto
        })
 
    # Solo se guardan los resultados de ESTUDIANTES (si un docente o administrador prueba el juego, no se guarda).
    # Se guarda una fila por pregunta; todas con la misma fecha para poder distinguir cada intento.
    es_estudiante = session.get('tipo') == 'estudiante'
    guardado = False
    if es_estudiante:
        ahora = datetime.now()
        try:
            for id_respuesta, acerto in por_guardar:
                insertar_resultado(
                    PUNTOS_POR_PREGUNTA if acerto else 0,
                    ahora, ahora, id_respuesta, juego[0], session['rol_id']
                )
            guardado = True
        except Exception as error:
            print("No se pudo guardar el resultado:", error)
            db.session.rollback()
 
    return jsonify({
        'puntaje': aciertos * PUNTOS_POR_PREGUNTA,
        'maximo': len(detalle) * PUNTOS_POR_PREGUNTA,
        'aciertos': aciertos,
        'total': len(detalle),
        'detalle': detalle,
        'guardado': guardado,
        'es_estudiante': es_estudiante
    })
 
#############################################################################

if __name__ == "__main__":
    app.run(debug=True)