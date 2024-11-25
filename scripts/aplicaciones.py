import platform
import json
import os
import subprocess
import re
from datetime import datetime

# Importa winreg solo si el sistema operativo es Windows
if platform.system() == "Windows":
    import winreg

# Obtiene una lista de aplicaciones instaladas en Windows con información detallada.
def obtener_aplicaciones_windows():
    aplicaciones = []
    rutas = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]

    def obtener_valor_registro(clave, nombre_valor):
        # Función auxiliar para obtener un valor del registro de Windows de manera segura
        try:
            return winreg.QueryValueEx(clave, nombre_valor)[0]
        except FileNotFoundError:
            return "Desconocido"

    for ruta in rutas:
        try:
            clave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ruta)
            for i in range(winreg.QueryInfoKey(clave)[0]):
                subclave = winreg.EnumKey(clave, i)
                subclave_ruta = f"{ruta}\\{subclave}"
                try:
                    subclave_abierta = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subclave_ruta)
                    nombre = obtener_valor_registro(subclave_abierta, "DisplayName")
                    version = obtener_valor_registro(subclave_abierta, "DisplayVersion")
                    fabricante = obtener_valor_registro(subclave_abierta, "Publisher")
                    ruta_instalacion = obtener_valor_registro(subclave_abierta, "InstallLocation")
                    fecha_instalacion = obtener_valor_registro(subclave_abierta, "InstallDate")
                    aplicaciones.append({
                        "nombre": nombre,
                        "version": version,
                        "fabricante": fabricante,
                        "ruta_instalacion": ruta_instalacion,
                        "fecha_instalacion": fecha_instalacion
                    })
                except FileNotFoundError:
                    continue
        except Exception as e:
            print(f"Error accediendo al registro: {e}")
    return aplicaciones

# Obtiene una lista de aplicaciones instaladas en Linux con información detallada.
def obtener_aplicaciones_linux():
    aplicaciones = []
    try:
        resultado = subprocess.run(['dpkg-query', '-W', '--showformat=${Package} ${Version} ${Architecture}\n'], stdout=subprocess.PIPE, text=True)
        paquetes = resultado.stdout.strip().split('\n')
        for paquete in paquetes:
            detalles = paquete.split(' ')
            if len(detalles) >= 3:
                aplicaciones.append({
                    "nombre": detalles[0],
                    "version": detalles[1],
                    "arquitectura": detalles[2],
                    "ruta_instalacion": "Desconocida",
                    "fecha_instalacion": "Desconocida"
                })
    except FileNotFoundError:
        print("dpkg-query no está disponible. Este script funciona en distribuciones basadas en Debian.")
    except subprocess.SubprocessError as e:
        print(f"Error ejecutando dpkg-query: {e}")
    return aplicaciones

# Obtiene una lista de aplicaciones instaladas en macOS con información detallada.
def obtener_aplicaciones_macos():
    aplicaciones = []
    try:
        resultado = subprocess.run(['system_profiler', 'SPApplicationsDataType'], stdout=subprocess.PIPE, text=True)
        lineas = resultado.stdout.split('\n')
        app_info = {}
        for linea in lineas:
            if "Location:" in linea:
                app_info['ruta_instalacion'] = linea.split(": ")[1].strip()
            elif "Name:" in linea:
                app_info['nombre'] = linea.split(": ")[1].strip()
            elif "Version:" in linea:
                app_info['version'] = linea.split(": ")[1].strip()
            elif "Obtained from:" in linea:
                app_info['fabricante'] = linea.split(": ")[1].strip()
            elif "Last Modified:" in linea:
                fecha_str = linea.split(": ")[1].strip()
                try:
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S %z")
                    app_info['fecha_actualizacion'] = fecha.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    app_info['fecha_actualizacion'] = "Desconocida"
                aplicaciones.append(app_info.copy())
    except subprocess.SubprocessError as e:
        print(f"Error al listar aplicaciones en macOS: {e}")
    return aplicaciones

# Función principal que detecta el sistema operativo y obtiene la lista de aplicaciones instaladas.
def main():
    sistema_operativo = platform.system()
    print(f"Detectado sistema operativo: {sistema_operativo}")
    aplicaciones = []

    if sistema_operativo == "Windows":
        aplicaciones = obtener_aplicaciones_windows()
    elif sistema_operativo == "Linux":
        aplicaciones = obtener_aplicaciones_linux()
    elif sistema_operativo == "Darwin":  # Darwin es el nombre base de macOS
        aplicaciones = obtener_aplicaciones_macos()
    else:
        print("Sistema operativo no soportado.")

    if aplicaciones:
        # Crear la carpeta de salida con la fecha actual
        json_folder = f"Archivos-JSON/{datetime.now().strftime('%Y-%m-%d')}"
        if not os.path.exists(json_folder):
            os.makedirs(json_folder)

        metadata = {
            "fecha_recoleccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "aplicaciones": aplicaciones
        }
        filepath = os.path.join(json_folder, "aplicaciones.json")
        with open(filepath, "w", encoding="utf-8") as archivo:
            json.dump(metadata, archivo, indent=4, ensure_ascii=False)
        print(f"Se ha generado el archivo '{filepath}' con la información de las aplicaciones instaladas.")
    else:
        print("No se encontraron aplicaciones o no se pudo acceder a la información.")
