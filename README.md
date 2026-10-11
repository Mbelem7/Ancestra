# Ancestra 
# Ancestra

Plataforma web educativa para preservar y difundir la memoria histórico-cultural del pueblo Mangue de Masaya, Nicaragua. Reúne en un solo lugar una biblioteca de documentos, una galería de imágenes y videos, un mapa de lugares de interés y juegos educativos que los docentes pueden crear y compartir con sus estudiantes.

Proyecto académico de la asignatura Administración Informática.

**Equipo:** [nombres de las integrantes]

## Módulos

| Módulo | Qué permite |
|---|---|
| **Biblioteca** | Consultar libros, documentos, cuentos, tesis y ensayos en PDF, clasificados por categoría |
| **Galería** | Ver imágenes y videos organizados en álbumes por categoría |
| **Mapa** | Ubicar en un mapa interactivo (Leaflet + OpenStreetMap) comunidades, bibliotecas y lugares de interés, con su información de contacto |
| **Juegos** | Los docentes crean plantillas de evaluación y reciben un código de acceso de 6 caracteres; los estudiantes entran con ese código, juegan y reciben su puntaje |
| **Administración** | Los administradores gestionan el contenido (documentos, imágenes y lugares) y aprueban las cuentas de docentes |

## Tecnologías

| Componente | Tecnología |
|---|---|
| Lenguaje y framework | Python + Flask |
| Plantillas | Jinja2 (HTML, CSS y JavaScript) |
| Acceso a datos | SQLAlchemy (Flask-SQLAlchemy) con psycopg2; consultas en SQL explícito con parámetros nombrados |
| Base de datos | PostgreSQL alojado en Supabase |
| Configuración | python-dotenv (variables de entorno) |
| Seguridad | Werkzeug (contraseñas con hash y nombres de archivo seguros) |
| Mapa | Leaflet + OpenStreetMap |
| Control de versiones y gestión | Git y GitHub; Trello para los sprints |

**Arquitectura:** monolito en capas (patrón MVC / MTV). Las rutas de Flask reciben la petición, validan los datos y los permisos, llaman a los módulos de acceso a datos y devuelven una plantilla.

## Estructura del repositorio

```
.
├── app.py                    Aplicación Flask: rutas, validaciones y permisos
├── crear_administrador.py    Script para crear la cuenta de administrador
├── requirements.txt          Dependencias de Python
├── .env.example              Modelo de las variables de entorno (sin datos reales)
├── modulos/                  Acceso a datos: un módulo por entidad
│   ├── archivos.py, categorias.py, autor.py
│   ├── lugares.py, ruta.py, alianza.py
│   ├── juegos.py, plantillas.py, preguntas.py, respuestas.py, resultados.py
│   └── persona.py, docente.py, estudiante.py, administrador.py
├── templates/                Páginas HTML (Jinja2)
│   └── juegos/               Pantallas para crear y jugar
└── static/                   Estilos, scripts, imágenes y documentos
```

## Instalación y ejecución

### Requisitos previos

- Python 3.10 o superior
- Un proyecto de [Supabase](https://supabase.com) con la base de datos creada (ver la sección *Base de datos*)

### Pasos

1. **Clonar el repositorio**

   ```bash
   git clone [URL del repositorio]
   cd [carpeta del repositorio]
   ```

2. **Crear y activar un entorno virtual**

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux o macOS
   source venv/bin/activate
   ```

3. **Instalar las dependencias**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar las variables de entorno.** Copia `.env.example` como `.env` y completa los valores:

   ```env
   user=
   password=
   host=
   port=
   dbname=
   SECRET_KEY=
   ```

   - `user`, `password`, `host`, `port` y `dbname` son los datos de conexión de tu proyecto de Supabase (en *Project Settings → Database*).
   - `SECRET_KEY` firma las sesiones de inicio de sesión. Genera una con:

     ```bash
     python -c "import secrets; print(secrets.token_hex(32))"
     ```

   > El archivo `.env` contiene credenciales y **no debe subirse al repositorio**.

5. **Comprobar las carpetas de archivos subidos.** Deben existir `static/assets/img` (imágenes y videos) y `static/assets/docs` (documentos PDF).

6. **Crear la cuenta de administrador**

   ```bash
   python crear_administrador.py
   ```

   El script pide los datos, encripta la contraseña y guarda la cuenta. Los administradores no se pueden registrar desde la página.

7. **Iniciar la aplicación**

   ```bash
   flask run
   ```

   Abre `http://127.0.0.1:5000` en el navegador. Al arrancar, la terminal muestra si la conexión con Supabase fue exitosa.

## Base de datos

PostgreSQL en Supabase, con 18 tablas relacionales (nombres en minúscula con guion bajo):

- **Personas y roles:** `persona`, `estudiante`, `docente`, `administrador`
- **Contenido cultural:** `archivo`, `categorias`, `autor`, `archivo_autor`
- **Territorio y alianzas:** `lugar`, `ruta`, `reunion`, `alianza`, `suscripcion`
- **Juegos:** `juego`, `plantilla`, `pregunta`, `respuesta`, `resultado`

Script de creación de las tablas: [ubicación del script SQL o enlace].

## Roles y permisos

| Rol | Puede |
|---|---|
| **Visitante** | Ver la biblioteca, la galería y el mapa |
| **Estudiante** | Lo anterior, y jugar con el código de acceso de un docente (su puntaje queda guardado) |
| **Docente** | Lo de un estudiante y, una vez **aprobado por un administrador**, crear plantillas de juegos y ver las suyas |
| **Administrador** | Todo lo anterior, gestionar documentos, imágenes y lugares, y aprobar o rechazar docentes |

Los docentes se registran desde la página y quedan en estado *pendiente* hasta que un administrador los aprueba en `/admin/docentes`.

## Rutas principales

| Ruta | Descripción | Acceso |
|---|---|---|
| `/` | Inicio | Público |
| `/biblioteca`, `/galeria`, `/mapa` | Consulta de contenido | Público |
| `/registro`, `/login`, `/logout` | Cuentas y sesión | Público |
| `/jugar` | Ingresar el código y jugar | Con sesión iniciada |
| `/crear`, `/mis-plantillas` | Crear plantillas de juegos y ver las propias | Docente aprobado o administrador |
| `/crear-documento`, `/crear-imagen`, `/crear-local` | Agregar contenido (y sus rutas de edición) | Administrador |
| `/admin/docentes` | Aprobar o rechazar docentes | Administrador |
| `/buscar_documento`, `/buscar_imagen`, `/buscar_lugar` | Búsqueda por coincidencia parcial; devuelven JSON | Público |

## Juegos

Se pueden crear plantillas de cuatro tipos: **verdadero y falso**, **selección múltiple**, **completar** y **unir con línea**.

La partida jugable está disponible para **verdadero y falso**: cada pregunta tiene un tiempo límite de 20 segundos, pasa a la siguiente al responder o al agotarse el tiempo, y el **servidor califica** (10 puntos por respuesta correcta). Las respuestas correctas nunca se envían al navegador. Los otros tres tipos permiten crear plantillas, y su pantalla de juego está en desarrollo.

## Seguridad

- Contraseñas almacenadas con hash, nunca en texto plano
- Sesiones con cookie firmada mediante clave secreta
- Control de acceso por rol en cada ruta protegida
- Consultas SQL con parámetros nombrados (previene la inyección SQL)
- Validación de datos y de tipos de archivo en el servidor
- Escape automático del contenido en las plantillas
- Calificación de los juegos en el servidor
- Credenciales y clave secreta en variables de entorno, fuera del repositorio

## Ramas

| Rama | Uso |
|---|---|
| `main` | Rama principal; en ella se desarrolló e integró el proyecto |
| `Dev` | Rama de desarrollo auxiliar |
| `frontend` | [Confirmar el nombre exacto] Interfaz: plantillas, estilos y scripts |

## Pendientes y mejoras previstas

- Protección contra formularios falsos (CSRF) y límite de intentos de inicio de sesión
- Recuperación de contraseña
- Pantallas de juego para selección múltiple, completar y unir con línea
- Vista de resultados para los docentes
- Módulos de reuniones y suscripciones
- Conectar la barra de búsqueda de la interfaz con las rutas de búsqueda
- Búsqueda de texto completo (Full-Text Search) de PostgreSQL
- Evolución a una API REST con un frontend independiente cuando el proyecto escale a más instituciones
