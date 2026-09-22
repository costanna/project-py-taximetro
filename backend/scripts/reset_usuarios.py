import os
import sys

import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("Falta DATABASE_URL. Ejecuta:")
    print('  DATABASE_URL="<la misma cadena que usa Render>" python reset_usuarios.py')
    sys.exit(1)

conexion = psycopg2.connect(DATABASE_URL)
try:
    with conexion.cursor() as cursor:
        cursor.execute("SELECT username FROM usuarios")
        usuarios = [fila[0] for fila in cursor.fetchall()]
        print(f"Usuarios encontrados en esta base: {usuarios or '(ninguno)'}")

        if not usuarios:
            print(
                "La tabla ya está vacía. Si /auth/registro sigue dando 409, "
                "esta no es la base que usa Render (revisa la cadena de conexión)."
            )
            sys.exit(0)

        respuesta = input("¿Borrar estos usuarios? (escribe 'si' para confirmar): ")
        if respuesta.strip().lower() != "si":
            print("Cancelado.")
            sys.exit(0)

        cursor.execute("DELETE FROM usuarios")
        conexion.commit()
        print("Usuarios borrados.")
finally:
    conexion.close()
