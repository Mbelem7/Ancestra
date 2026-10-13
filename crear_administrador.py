"""
Crea una cuenta de ADMINISTRADOR en la base de datos.

Cómo usarlo (con el entorno virtual activado, desde la carpeta del proyecto):

    python crear_administrador.py

Te pregunta los datos, encripta la contraseña y guarda la persona y su perfil de administrador.
"""
from getpass import getpass
from datetime import datetime
from werkzeug.security import generate_password_hash

from app import app
from modulos.persona import insertar_persona, obtener_persona_por_correo, eliminar_persona
from modulos.administrador import insertar_administrador


def pedir(texto, obligatorio=True):
    while True:
        valor = input(texto).strip()
        if valor or not obligatorio:
            return valor
        print("  Este dato es obligatorio.")


def main():
    print("=== Crear cuenta de administrador ===")
    nombre_1 = pedir("Primer nombre: ")
    apellido_1 = pedir("Primer apellido: ")
    correo = pedir("Correo (con este iniciará sesión): ").lower()
    nombre_usuario = pedir("Nombre de usuario: ")

    while True:
        contrasena = getpass("Contraseña (mínimo 8 caracteres): ")
        if len(contrasena) < 8:
            print("  Debe tener al menos 8 caracteres.")
            continue
        if contrasena != getpass("Repite la contraseña: "):
            print("  No coinciden, intenta de nuevo.")
            continue
        break

    with app.app_context():
        if obtener_persona_por_correo(correo):
            print("\nYa existe una cuenta con ese correo. No se creó nada.")
            return

        ahora = datetime.now()
        id_persona = insertar_persona(
            nombre_1, None, apellido_1, None, None, correo,
            'administrador', 'activo', generate_password_hash(contrasena), ahora, ahora
        )
        try:
            id_administrador = insertar_administrador(id_persona, nombre_usuario)
        except Exception as error:
            eliminar_persona(id_persona)
            print("\nNo se pudo crear el perfil de administrador:", error)
            return

    print(f"\n✔ Administrador creado (id {id_administrador}). Ya puede iniciar sesión con {correo}.")


if __name__ == "__main__":
    main()