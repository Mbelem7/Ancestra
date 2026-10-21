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

# Evita errores y esperas largas por conexiones que se cortan cuando llevan un rato sin usarse
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,        # antes de usar una conexión, comprueba que siga viva
    'pool_recycle': 280,          # renueva las conexiones cada ~5 minutos
    'connect_args': {
        'keepalives': 1,              # envía señales para que la red no cierre la conexión por inactividad
        'keepalives_idle': 10,        # primera señal tras 10 s sin uso
        'keepalives_interval': 5,     # y luego una cada 5 s
        'keepalives_count': 3,
        'connect_timeout': 10,        # si no logra conectar en 10 s, falla en vez de quedarse esperando
    },
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
from modulos import seguridad
import random
import unicodedata
import string
import re
import uuid
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

     # Norma 2.1: complejidad de la contraseña (2.1.1) y que no esté en filtraciones conocidas (2.1.3)
    if contrasena != confirmar:
        erroresR.append("Las contraseñas no coinciden.")
    else:
        nombre_completo = f"{nombre_1} {nombre_2} {apellido_1} {apellido_2}"
        erroresR += seguridad.evaluar_y_registrar(contrasena, correo, nombre_completo, 'registro')

    if not erroresR:
        mensaje_filtracion = seguridad.revisar_filtracion(contrasena, correo, 'registro')
        if mensaje_filtracion:
            erroresR.append(mensaje_filtracion)

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
    session['correo'] = persona[3]

    # Norma 2.1: toda contraseña caduca y debe cumplir la complejidad actual; si no, debe cambiarla antes de seguir
    ultimo_cambio = persona[8] or persona[7] or datetime.now()
    session['contrasena_vence'] = seguridad.vencimiento(ultimo_cambio).isoformat()
    if seguridad.dias_para_vencer(ultimo_cambio) <= 0:
        session['debe_cambiar_contrasena'] = 'caducada'
    elif seguridad.evaluar_contrasena(contrasena, persona[3], f"{persona[1]} {persona[2]}"):
        session['debe_cambiar_contrasena'] = 'no_cumple'
    if session.get('debe_cambiar_contrasena'):
        return redirect(url_for('cambiar_contrasena'))

    return redirect(destino_seguro(siguiente) or url_for('index'))


#LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

########################################################################
#NORMA DE CONTRASEÑAS (2.1): complejidad, caducidad y filtraciones conocidas
RUTAS_LIBRES_SI_DEBE_CAMBIAR = ('cambiar_contrasena', 'logout', 'static')


@app.before_request
def exigir_cambio_de_contrasena():
    # Si su contraseña caducó o ya no cumple la norma, la persona solo puede cambiarla o cerrar sesión
    if session.get('debe_cambiar_contrasena') and request.endpoint not in RUTAS_LIBRES_SI_DEBE_CAMBIAR:
        return redirect(url_for('cambiar_contrasena'))


@app.context_processor
def datos_de_seguridad():
    # Lo que reciben todas las pantallas: la norma (para el registro) y el aviso "tu contraseña vence en N días"
    datos = {'norma_contrasena': {'longitud': seguridad.LONGITUD_MINIMA}, 'aviso_contrasena': None}
    vence = session.get('contrasena_vence')
    if vence and request.endpoint != 'cambiar_contrasena':
        dias = seguridad.dias_hasta_vencimiento(datetime.fromisoformat(vence))
        if 0 < dias <= seguridad.AVISO_EN_PANTALLA_DIAS:
            datos['aviso_contrasena'] = dias
    return datos


@app.route('/cambiar-contrasena', methods=['GET', 'POST'])
@login_required
def cambiar_contrasena():
    motivo = session.get('debe_cambiar_contrasena')    # 'caducada', 'no_cumple' o None (cambio voluntario)

    if request.method == 'GET':
        return render_template('cambiar_contrasena.html', motivo=motivo)

    actual = request.form.get('actual', '')
    nueva = request.form.get('nueva', '')
    confirmar = request.form.get('confirmar', '')
    correo = session.get('correo', '')
    errores = []

    hash_actual = obtener_contrasena_por_id(session['persona_id'])
    if not hash_actual or not check_password_hash(hash_actual, actual):
        errores.append("La contraseña actual no es correcta.")
    elif check_password_hash(hash_actual, nueva):
        errores.append("La contraseña nueva debe ser distinta de la actual.")

    if nueva != confirmar:
        errores.append("Las contraseñas nuevas no coinciden.")
    else:
        errores += seguridad.evaluar_y_registrar(nueva, correo, session.get('nombre', ''), 'cambio')

    # 2.1.3: solo si todo lo demás está bien se consulta si la contraseña apareció en filtraciones
    if not errores:
        mensaje_filtracion = seguridad.revisar_filtracion(nueva, correo, 'cambio')
        if mensaje_filtracion:
            errores.append(mensaje_filtracion)

    if errores:
        return render_template('cambiar_contrasena.html', motivo=motivo, errores=errores)

    ahora = datetime.now()
    actualizar_contrasena(session['persona_id'], generate_password_hash(nueva), ahora)
    session.pop('debe_cambiar_contrasena', None)
    session['contrasena_vence'] = seguridad.vencimiento(ahora).isoformat()
    return render_template('cambiar_contrasena.html', exito=True)


# 2.1.2: rutina diaria. Se programa con cron (Linux) o con el Programador de tareas (Windows):
#   flask notificar-caducidad
@app.cli.command('notificar-caducidad')
def notificar_caducidad():
    """Avisa por correo a quien su contraseña está por vencer (14, 7, 3 y 1 días antes, y el día que vence)."""
    ahora = datetime.now()
    personas = obtener_personas_para_aviso_caducidad(seguridad.limite_para_avisos(ahora))
    # persona: (id_persona, nombre_1, apellido_1, correo, ultimo_cambio)
    enviados = 0
    sin_enviar = 0
    for persona in personas:
        dias = seguridad.dias_para_vencer(persona[4], ahora)
        if dias not in seguridad.AVISOS_DIAS:
            continue
        asunto, cuerpo = seguridad.mensaje_de_caducidad(persona[1], dias)
        if seguridad.enviar_correo(persona[3], asunto, cuerpo):
            enviados += 1
            seguridad.registrar_validacion('caducidad', persona[3], 'aviso_enviado', f'vence en {dias} día(s)')
        else:
            sin_enviar += 1
            print(f"[sin enviar] {persona[3]}: su contraseña vence en {dias} día(s)")
            seguridad.registrar_validacion('caducidad', persona[3], 'aviso_no_enviado', f'vence en {dias} día(s)')
    print(f"Avisos de caducidad: {enviados} enviados, {sin_enviar} sin enviar.")

#ADMIN - APROBAR DOCENTES
# Colores de cada tipo de juego en las gráficas (los mismos de las piezas de puzzle)
COLORES_TIPO = {'verdadero_falso': '#FFC565', 'seleccion_multiple': '#BECC29', 'completar': '#10C6D9', 'union': '#F22C0C'}
NOMBRES_CORTOS = {'verdadero_falso': 'V/F', 'seleccion_multiple': 'Múltiple', 'completar': 'Completar', 'union': 'Unir'}


def repartir_por_tipo(conteo):
    # conteo: {tipo: cantidad}. Devuelve (filas, total): una fila por cada tipo de juego (también los que
    # tienen 0) con su porcentaje entero, que siempre suma 100, y los datos para dibujar el pastel.
    total = sum(conteo.get(tipo, 0) for tipo in JUEGOS_DISPONIBLES)
    filas = []
    for tipo in JUEGOS_DISPONIBLES:
        cantidad = conteo.get(tipo, 0)
        filas.append({
            'tipo': tipo,
            'nombre': NOMBRES_TIPO[tipo],
            'cantidad': cantidad,
            'exacto': cantidad * 100 / total if total else 0,
            'color': COLORES_TIPO[tipo]
        })

    # Porcentajes enteros que suman 100 (los que faltan se reparten entre los de mayor decimal)
    for fila in filas:
        fila['porcentaje'] = int(fila['exacto'])
    faltan = 100 - sum(fila['porcentaje'] for fila in filas) if total else 0
    for fila in sorted(filas, key=lambda f: f['exacto'] - int(f['exacto']), reverse=True)[:faltan]:
        fila['porcentaje'] += 1

    # Dónde empieza y cuánto mide cada rebanada (el círculo completo mide 100; se deja un huequito entre rebanadas)
    con_datos = sum(1 for fila in filas if fila['cantidad'])
    espacio = 0.8 if con_datos > 1 else 0
    acumulado = 0
    for fila in filas:
        fila['dash'] = round(max(fila['exacto'] - espacio, 0.3), 3) if fila['cantidad'] else 0
        fila['desfase'] = round(25 - acumulado, 3)      # 25 = empezar arriba y avanzar hacia la derecha
        acumulado += fila['exacto']

    return filas, total


@app.route('/admin/docentes')
@rol_requerido('administrador')
def admin_docentes():
    docentes = obtener_docentes()
    # d: (id_docente, estado_verificacion, id_persona, nombre_1, nombre_2, apellido_1, apellido_2,
    #     fecha_nacimiento, correo, estado)
    orden = {'pendiente': 0, 'rechazado': 1, 'verificado': 2}
    docentes = sorted(docentes, key=lambda d: orden.get(d[1], 3))

    # Cuántas plantillas creó cada docente y de qué tipo: {id_docente: {'total': n, 'tipos': [...]}}
    por_docente = {}
    for docente_id, tipo, cantidad in contar_plantillas_por_docente():
        por_docente.setdefault(docente_id, {})[tipo] = cantidad
    plantillas_de = {}
    for docente_id, tipos in por_docente.items():
        plantillas_de[docente_id] = {
            'total': sum(tipos.values()),
            'tipos': [{'tipo': t, 'nombre': NOMBRES_TIPO[t], 'corto': NOMBRES_CORTOS[t], 'cantidad': tipos[t]}
                      for t in JUEGOS_DISPONIBLES if t in tipos]
        }

    # El pastel: qué tipo de plantilla se crea más
    pastel, total_plantillas = repartir_por_tipo(dict(contar_plantillas_por_tipo()))
    mas_creadas = []
    if total_plantillas:
        maximo = max(fila['cantidad'] for fila in pastel)
        mas_creadas = [fila for fila in pastel if fila['cantidad'] == maximo]

    resumen = {
        'docentes_activos': sum(1 for d in docentes if d[1] == 'verificado' and d[9] == 'activo'),
        'docentes_pendientes': sum(1 for d in docentes if d[1] == 'pendiente'),
        'estudiantes_activos': contar_estudiantes_activos(),
        'plantillas': total_plantillas
    }
    return render_template('admin_docentes.html', docentes=docentes, plantillas_de=plantillas_de,
                           pastel=pastel, mas_creadas=mas_creadas, resumen=resumen)


@app.route('/admin/docentes/<int:id_docente>/estado', methods=['POST'])
@rol_requerido('administrador')
def admin_docente_estado(id_docente):
    nuevo_estado = request.form.get('estado')
    if nuevo_estado in ('pendiente', 'verificado', 'rechazado') and obtener_un_docente(id_docente):
        actualizar_estado_verificacion(id_docente, nuevo_estado)
    return redirect(url_for('admin_docentes'))

@app.route('/admin/docentes/<int:id_docente>')
@rol_requerido('administrador')
def admin_docente_detalle(id_docente):
    docente = obtener_docente_detalle(id_docente)
    # docente: (id_docente, estado_verificacion, id_persona, nombre_1, nombre_2, apellido_1,
    #           apellido_2, fecha_nacimiento, correo, estado, fecha_creacion)
    if not docente:
        return redirect(url_for('admin_docentes'))

    edad = None
    nacimiento = docente[7]
    if nacimiento:
        hoy = date.today()
        edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))

        # Las plantillas que creó este docente (el administrador puede abrir sus preguntas y sus resultados)
    plantillas = obtener_plantillas_resumen(docente[0])
    # plantilla: (id_plantilla, codigo_acceso, fecha_creacion, nombre, descripcion, tipo, estado, total_preguntas)
    por_tipo = {}
    for plantilla in plantillas:
        por_tipo[plantilla[5]] = por_tipo.get(plantilla[5], 0) + 1
    tipos = [{'tipo': t, 'nombre': NOMBRES_TIPO[t], 'cantidad': por_tipo[t]} for t in JUEGOS_DISPONIBLES if t in por_tipo]

    return render_template('admin_docente_detalle.html', d=docente, edad=edad, plantillas=plantillas, tipos=tipos)

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

#NOMBRE ÚNICO PARA LOS ARCHIVOS SUBIDOS
def nombre_archivo_unico(nombre_original):
    # Mantiene la extensión y agrega un código único, para que dos archivos con el mismo nombre no se pisen
    extension = nombre_original.rsplit('.', 1)[1].lower() if '.' in nombre_original else ''
    base = secure_filename(nombre_original.rsplit('.', 1)[0]) or 'archivo'
    return f"{uuid.uuid4().hex[:8]}_{base}.{extension}"

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
@app.route('/memorias')
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
 
        filename = nombre_archivo_unico(file.filename)
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
        return redirect(url_for('biblioteca'))
 
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
            filename = nombre_archivo_unico(file.filename)
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
        return redirect(url_for('biblioteca'))
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
@app.route('/vestigios')
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
 
        filename = nombre_archivo_unico(file.filename)
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
        return redirect(url_for('galeria'))
 
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
            filename = nombre_archivo_unico(file.filename)
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
        return redirect(url_for('galeria'))
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
@app.route('/huellas')
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
            'editar': url_for('editar_lugar', id_lugar=l[0]) if session.get('tipo') == 'administrador' else None
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
        return redirect(url_for('mapa'))
 
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
        return redirect(url_for('mapa'))
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
 
            # En verdadero y falso las respuestas son siempre estas dos (no las escribe el docente)
            respuestas = ['Verdadero', 'Falso']

            if correcta not in ('1', '2'):
                erroresP.append(f"Falta marcar si la afirmación {i} es verdadera o falsa.")
 
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
                            nombre=nombre, codigo_acceso=codigo_acceso,
                            tipo='verdadero_falso')
 
 
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
                            nombre=nombre, codigo_acceso=codigo_acceso,
                            tipo='seleccion_multiple')
 
 
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
            elif len(re.findall(r'_+', enunciado)) != 1:
                erroresP.append(f"La pregunta {i} debe tener un espacio en blanco: escribe _ donde va la respuesta.")
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
                            nombre=nombre, codigo_acceso=codigo_acceso,
                            tipo='completar')
 
 
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
                            nombre=nombre, codigo_acceso=codigo_acceso,
                            tipo='union')
 
 #############################################################################
#MIS PLANTILLAS
@app.route('/mis-plantillas')
@puede_crear_plantillas
def mis_plantillas():
    docente_id, administrador_id = ids_de_creador()   # cada quien ve solo las plantillas que creó él mismo
    plantillas = obtener_plantillas_resumen(docente_id, administrador_id)
    return render_template('juegos/mis_plantillas.html', plantillas=plantillas)

#VER UNA PLANTILLA CON SUS PREGUNTAS Y RESPUESTAS
@app.route('/mis-plantillas/<int:id_plantilla>')
@puede_crear_plantillas
def ver_plantilla(id_plantilla):
    plantilla = obtener_una_plantilla(id_plantilla)
    # plantilla: (id_plantilla, codigo_acceso, fecha_creacion, fecha_modificacion,
    #             juego_id, docente_id, administrador_id)
    if not plantilla:
        return redirect(url_for('mis_plantillas'))

    # Un docente solo puede ver SUS plantillas (aquí se muestran las respuestas correctas);
    # el administrador puede ver todas
    docente_id, _ = ids_de_creador()
    if session.get('tipo') != 'administrador' and plantilla[5] != docente_id:
        return render_template('acceso_denegado.html'), 403

    juego = obtener_un_juego(plantilla[4])
    # juego: (id_juego, nombre, descripcion, tipo, fecha_creacion,
    #         fecha_modificacion, administrador_id, estado)

    preguntas = []
    for pregunta in sorted(obtener_preguntas_por_plantilla(id_plantilla), key=lambda p: p[0]):
        respuestas = sorted(obtener_respuestas_por_pregunta(pregunta[0]), key=lambda r: r[0])
        preguntas.append((pregunta, respuestas))

    return render_template(
        'juegos/ver_plantilla.html',
        plantilla=plantilla,
        juego=juego,
        preguntas=preguntas,
        nombre_tipo=NOMBRES_TIPO.get(juego[3], juego[3])
    )

#############################################################################
#PANELES DE RESULTADOS
def intento_oficial(filas):
    # La evaluación se hace una sola vez. Si por pruebas anteriores hubiera más de un intento, cuenta el PRIMERO
    if not filas:
        return []
    primera = min(f[2] for f in filas)
    return [f for f in filas if f[2] == primera]


def ya_realizo_la_evaluacion(juego_id):
    # Solo los estudiantes tienen un único intento; docentes y administradores pueden probar el juego
    if session.get('tipo') != 'estudiante':
        return False
    return bool(obtener_resultados_de_estudiante_en_juego(session['rol_id'], juego_id))


def datos_de_intento(fecha, puntaje, preguntas):
    # Un intento listo para mostrar: puntaje, máximo posible, porcentaje y nivel (el nivel decide el color)
    puntaje = int(puntaje)
    maximo = int(preguntas) * PUNTOS_POR_PREGUNTA
    porcentaje = round(puntaje * 100 / maximo) if maximo else 0
    nivel = 'alto' if porcentaje >= 80 else ('medio' if porcentaje >= 50 else 'bajo')
    return {'fecha': fecha, 'puntaje': puntaje, 'maximo': maximo, 'porcentaje': porcentaje, 'nivel': nivel}


#RESULTADOS DE UNA PLANTILLA (panel del docente: solo ve el puntaje de cada estudiante)
@app.route('/mis-plantillas/<int:id_plantilla>/resultados')
@puede_crear_plantillas
def resultados_plantilla(id_plantilla):
    plantilla = obtener_una_plantilla(id_plantilla)
    # plantilla: (id_plantilla, codigo_acceso, fecha_creacion, fecha_modificacion,
    #             juego_id, docente_id, administrador_id)
    if not plantilla:
        return redirect(url_for('mis_plantillas'))

    # Un docente solo ve los resultados de SUS plantillas; el administrador ve todos
    docente_id, _ = ids_de_creador()
    if session.get('tipo') != 'administrador' and plantilla[5] != docente_id:
        return render_template('acceso_denegado.html'), 403

    juego = obtener_un_juego(plantilla[4])
    intentos = obtener_intentos_por_juego(plantilla[4])
    # intentos: (estudiante_id, nombre_1, nombre_2, apellido_1, apellido_2, correo,
    #            fecha, puntaje_total, cantidad_de_preguntas)

    # Cada estudiante tiene UN intento (si por pruebas anteriores hubiera más, cuenta el primero)
    por_estudiante = {}
    for fila in intentos:
        intento = datos_de_intento(fila[6], fila[7], fila[8])
        actual = por_estudiante.get(fila[0])
        if actual is None or intento['fecha'] < actual['intento']['fecha']:
            por_estudiante[fila[0]] = {
                'nombre': ' '.join(parte for parte in (fila[1], fila[2], fila[3], fila[4]) if parte),
                'correo': fila[5],
                'intento': intento
            }

    # Primero quien sacó el mejor puntaje; si empatan, por nombre
    participantes = sorted(por_estudiante.values(), key=lambda e: (-e['intento']['puntaje'], e['nombre']))

    resumen = {
        'participantes': len(participantes),
        'promedio': round(sum(e['intento']['porcentaje'] for e in participantes) / len(participantes)) if participantes else 0,
        'mejor': max((e['intento']['porcentaje'] for e in participantes), default=0),
        'menor': min((e['intento']['porcentaje'] for e in participantes), default=0)
    }

    return render_template(
        'juegos/resultados_plantilla.html',
        plantilla=plantilla,
        juego=juego,
        participantes=participantes,
        resumen=resumen,
        nombre_tipo=NOMBRES_TIPO.get(juego[3], juego[3])
    )


#MIS RESULTADOS (panel del estudiante: una tarjeta por plantilla que hizo)
@app.route('/mis-resultados')
@rol_requerido('estudiante')
def mis_resultados():
    intentos = obtener_intentos_por_estudiante(session['rol_id'])
    # intentos: (juego_id, nombre_del_juego, tipo, fecha, puntaje_total, cantidad_de_preguntas)

    # Un intento por plantilla (si por pruebas anteriores hubiera más, cuenta el primero)
    por_juego = {}
    for fila in intentos:
        intento = datos_de_intento(fila[3], fila[4], fila[5])
        actual = por_juego.get(fila[0])
        if actual is None or intento['fecha'] < actual['intento']['fecha']:
            por_juego[fila[0]] = {
                'id_juego': fila[0],
                'nombre': fila[1],
                'tipo': NOMBRES_TIPO.get(fila[2], fila[2]),
                'tipo_clave': fila[2],
                'intento': intento
            }

    # La plantilla hecha más recientemente queda primero
    plantillas = sorted(por_juego.values(), key=lambda p: p['intento']['fecha'], reverse=True)

    return render_template('juegos/mis_resultados.html', plantillas=plantillas)


#MI RESULTADO EN UNA PLANTILLA (el estudiante revisa qué respondió bien y mal)
@app.route('/mis-resultados/<int:id_juego>')
@rol_requerido('estudiante')
def mi_resultado(id_juego):
    juego = obtener_un_juego(id_juego)
    filas = []
    if juego:
        filas = intento_oficial(obtener_resultados_de_estudiante_en_juego(session['rol_id'], id_juego))
        # filas: (id_resultado, puntaje, fecha_creacion, fecha_modificacion, respuesta_id, respuesta_texto),
        #        una por pregunta
    if not filas:
        return redirect(url_for('mis_resultados'))

    # Pregunta por pregunta: la fila 1 es la pregunta 1, y así (se crearon en ese orden)
    preguntas = sorted(obtener_preguntas_por_juego(id_juego), key=lambda p: p[0])
    respuestas_de = {p[0]: obtener_respuestas_por_pregunta(p[0]) for p in preguntas}
    todas = {r[0]: r for rs in respuestas_de.values() for r in rs}    # en "unir" la elegida puede ser de otra pareja

    detalle = []
    for indice, pregunta in enumerate(preguntas):
        correcta = next((r for r in respuestas_de[pregunta[0]] if r[2] == 'correcta'), None)
        fila = filas[indice] if indice < len(filas) else None

        if fila is None:
            tu_respuesta = None
        elif juego[3] == 'completar':
            tu_respuesta = fila[5]                      # lo que escribió
        else:
            elegida = todas.get(fila[4]) if fila[4] is not None else None
            tu_respuesta = elegida[1] if elegida else None

        detalle.append({
            'enunciado': pregunta[1],
            'tu_respuesta': tu_respuesta,
            'correcta': correcta[1] if correcta else None,
            'acerto': fila is not None and fila[1] > 0
        })

    intento = datos_de_intento(filas[0][2], sum(f[1] for f in filas), len(filas))

    return render_template(
        'juegos/mi_resultado.html',
        juego=juego,
        intento=intento,
        detalle=detalle,
        aciertos=sum(1 for d in detalle if d['acerto']),
        nombre_tipo=NOMBRES_TIPO.get(juego[3], juego[3])
    )

#############################################################################
#JUGAR
TIEMPO_POR_PREGUNTA = 20      # (el valor de siempre; ya casi no se usa)
PUNTOS_POR_PREGUNTA = 10      # puntos por cada respuesta correcta
JUEGOS_DISPONIBLES = ['verdadero_falso', 'seleccion_multiple', 'completar', 'union']
NOMBRES_TIPO = {
    'verdadero_falso': 'Verdadero y Falso',
    'seleccion_multiple': 'Selección múltiple',
    'completar': 'Completar',
    'union': 'Unir con línea'
}
# Segundos que tiene el estudiante en cada tipo de juego.
# En "union" son segundos POR PAREJA: el tiempo total es ese número por la cantidad de parejas.
TIEMPOS_POR_TIPO = {
    'verdadero_falso': 20,
    'seleccion_multiple': 30,
    'completar': 40,
    'union': 30
}
# La pantalla de la partida de cada tipo de juego
PANTALLAS_DE_PARTIDA = {
    'verdadero_falso': 'juegos/jugarvyf.html',
    'seleccion_multiple': 'juegos/jugarmult.html',
    'completar': 'juegos/jugarcomp.html',
    'union': 'juegos/jugarun.html'
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
 
def normalizar_respuesta(texto, ignorar_articulo=False):
    # Para comparar lo que escribe el estudiante con la respuesta correcta:
    # no importan las mayúsculas, los espacios de más ni las tildes (pero la ñ SÍ cuenta: año no es ano).
    # Con ignorar_articulo=True tampoco importa el artículo del principio: "El Güegüense" = "Güegüense"
    texto = ' '.join(str(texto).split()).lower().replace('ñ', '\0')
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    if ignorar_articulo:
        texto = re.sub(r'^(el|la|los|las|un|una|unos|unas)\s+', '', texto)
    return texto.replace('\0', 'ñ')

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
        # La evaluación se hace una sola vez: si ya la hizo, se le muestra su resultado
    if ya_realizo_la_evaluacion(plantilla[4]):
        return redirect(url_for('mi_resultado', id_juego=plantilla[4]))
 
    return redirect(url_for('jugar_plantilla', id_plantilla=plantilla[0]))
 
 
#PASO 2: pantalla con la información del juego y el botón "Jugar"
@app.route('/jugar/<int:id_plantilla>')
@login_required
def jugar_plantilla(id_plantilla):
    datos = cargar_plantilla_activa(id_plantilla)
    if not datos:
        return render_template('juegos/jugar.html', error="Esta plantilla no está disponible.")
    plantilla, juego = datos

    if ya_realizo_la_evaluacion(juego[0]):
        return redirect(url_for('mi_resultado', id_juego=juego[0]))

    preguntas = obtener_preguntas_por_plantilla(id_plantilla)
    tiempo = TIEMPOS_POR_TIPO.get(juego[3], TIEMPO_POR_PREGUNTA)
    return render_template(
        'juegos/plantilla_encontrada.html',
        juego=juego,
        id_plantilla=id_plantilla,
        total_preguntas=len(preguntas),
        tiempo=tiempo,
        tiempo_total=tiempo * len(preguntas),    # solo se usa en "Unir con línea"
        nombre_tipo=NOMBRES_TIPO.get(juego[3], juego[3]),
        disponible=(juego[3] in JUEGOS_DISPONIBLES and len(preguntas) > 0),
        es_estudiante=(session.get('tipo') == 'estudiante')
    )


#PASO 3: la partida (cada tipo de juego tiene su propia pantalla)
@app.route('/jugar/<int:id_plantilla>/partida')
@login_required
def jugar_partida(id_plantilla):
    datos = cargar_plantilla_activa(id_plantilla)
    if not datos:
        return redirect(url_for('jugar'))
    plantilla, juego = datos
    tipo = juego[3]

    if tipo not in JUEGOS_DISPONIBLES:
        return redirect(url_for('jugar_plantilla', id_plantilla=id_plantilla))

    # La evaluación se hace una sola vez
    if ya_realizo_la_evaluacion(juego[0]):
        return redirect(url_for('mi_resultado', id_juego=juego[0]))

    lista = sorted(obtener_preguntas_por_plantilla(id_plantilla), key=lambda p: p[0])
    if not lista:
        return redirect(url_for('jugar_plantilla', id_plantilla=id_plantilla))

    # Al navegador solo se le manda lo que necesita para jugar, NUNCA cuál es la respuesta correcta
    tiempo = TIEMPOS_POR_TIPO.get(tipo, TIEMPO_POR_PREGUNTA)
    contenido = {'tiempo': tiempo}

    if tipo in ('verdadero_falso', 'seleccion_multiple'):
        preguntas = []
        for pregunta in lista:
            opciones = [
                {'id': r[0], 'texto': r[1]}
                for r in sorted(obtener_respuestas_por_pregunta(pregunta[0]), key=lambda r: r[0])
            ]
            preguntas.append({'id': pregunta[0], 'enunciado': pregunta[1], 'opciones': opciones})
        contenido['preguntas'] = preguntas

    elif tipo == 'completar':
        # Solo el enunciado: la respuesta correcta NO viaja al navegador
        contenido['preguntas'] = [{'id': p[0], 'enunciado': p[1]} for p in lista]

    elif tipo == 'union':
        # Izquierda: el elemento de cada pareja. Derecha: sus parejas, MEZCLADAS para que el orden no delate la respuesta
        izquierda = [{'id': p[0], 'texto': p[1]} for p in lista]
        derecha = []
        for pregunta in lista:
            respuestas = obtener_respuestas_por_pregunta(pregunta[0])
            if respuestas:
                derecha.append({'id': respuestas[0][0], 'texto': respuestas[0][1]})
        random.shuffle(derecha)
        contenido['izquierda'] = izquierda
        contenido['derecha'] = derecha
        contenido['tiempo_total'] = tiempo * len(lista)

    # Para un estudiante, el intento se cuenta desde que abre la evaluación: se crea una fila por pregunta
    # (con 0 puntos y sin respuesta). Al terminar se completan; si cierra la página, lo que falte queda en 0.
    if session.get('tipo') == 'estudiante':
        ahora = datetime.now()
        for _ in lista:
            insertar_resultado(0, ahora, ahora, None, juego[0], session['rol_id'])

    return render_template(
        PANTALLAS_DE_PARTIDA[tipo],
        juego=juego,
        id_plantilla=id_plantilla,
        **contenido
    )


#PASO 4: el servidor califica lo que el estudiante respondió (y lo guarda si es estudiante)
@app.route('/jugar/<int:id_plantilla>/resultado', methods=['POST'])
@login_required
def jugar_resultado(id_plantilla):
    datos = cargar_plantilla_activa(id_plantilla)
    if not datos:
        return jsonify({'error': 'Plantilla no disponible'}), 404
    plantilla, juego = datos
    tipo = juego[3]

    es_estudiante = session.get('tipo') == 'estudiante'

    # Un estudiante solo puede enviar la evaluación que abrió, y una sola vez
    filas = []
    if es_estudiante:
        filas = intento_oficial(obtener_resultados_de_estudiante_en_juego(session['rol_id'], juego[0]))
        if not filas:
            return jsonify({'error': 'Primero debes abrir la evaluación.'}), 400
        if any(f[3] > f[2] for f in filas):      # fecha_modificacion > fecha_creacion: ya la envió
            return jsonify({'error': 'Ya enviaste esta evaluación.'}), 409

    # elegidas: {"id_pregunta": lo que respondió, ...} (null si no alcanzó a responder).
    # Lo que respondió es el id de una respuesta (V/F, múltiple y unir) o el texto que escribió (completar)
    cuerpo = request.get_json(silent=True)
    elegidas = cuerpo.get('respuestas', {}) if isinstance(cuerpo, dict) else {}
    if not isinstance(elegidas, dict):
        elegidas = {}

    lista = sorted(obtener_preguntas_por_plantilla(id_plantilla), key=lambda p: p[0])
    respuestas_de = {p[0]: obtener_respuestas_por_pregunta(p[0]) for p in lista}
    todas = {r[0]: r for rs in respuestas_de.values() for r in rs}     # en "unir" la elegida puede ser de otra pareja

    detalle = []
    por_guardar = []   # (id de la respuesta o None, texto escrito o None, si acertó), una por pregunta
    aciertos = 0
    for pregunta in lista:
        respuestas = respuestas_de[pregunta[0]]
        # respuesta: (id_respuesta, respuesta, tipo, fecha_creacion, fecha_modificacion,
        #             pregunta_id, juego_id, administrador_id)
        correcta = next((r for r in respuestas if r[2] == 'correcta'), None)
        enviada = elegidas.get(str(pregunta[0]))

        id_guardar = None
        texto_guardar = None
        tu_respuesta = None

        if tipo == 'completar':
            texto = enviada.strip()[:200] if isinstance(enviada, str) else ''
            if texto:
                texto_guardar = tu_respuesta = texto
            acerto = bool(texto) and correcta is not None and normalizar_respuesta(texto, True) == normalizar_respuesta(correcta[1], True)
            if acerto:
                id_guardar = correcta[0]
        else:
            if tipo == 'union':
                # Puede ser la pareja de OTRA fila; si dos parejas tienen el mismo texto, cualquiera de las dos vale
                elegida = todas.get(enviada) if isinstance(enviada, int) else None
                acerto = (elegida is not None and correcta is not None and
                          (elegida[0] == correcta[0] or normalizar_respuesta(elegida[1]) == normalizar_respuesta(correcta[1])))
            else:
                # Solo vale si la respuesta elegida pertenece a ESTA pregunta
                elegida = next((r for r in respuestas if r[0] == enviada), None)
                acerto = elegida is not None and correcta is not None and elegida[0] == correcta[0]
            if elegida is not None:
                id_guardar = elegida[0]
                tu_respuesta = elegida[1]

        if acerto:
            aciertos += 1

        por_guardar.append((id_guardar, texto_guardar, acerto))
        detalle.append({
            'enunciado': pregunta[1],
            'tu_respuesta': tu_respuesta,
            'correcta': correcta[1] if correcta else None,
            'acerto': acerto
        })

    # Solo se guardan los resultados de ESTUDIANTES (si un docente o administrador prueba el juego, no se guarda).
    # Se completan las filas que se crearon al abrir la evaluación: la fila 1 es la pregunta 1, y así.
    guardado = False
    if es_estudiante:
        ahora = datetime.now()
        try:
            for fila, (id_respuesta, texto, acerto) in zip(filas, por_guardar):
                registrar_respuesta_en_resultado(
                    fila[0], PUNTOS_POR_PREGUNTA if acerto else 0, id_respuesta, ahora, texto
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