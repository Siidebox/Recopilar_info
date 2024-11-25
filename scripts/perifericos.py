import platform
import json
import os
import subprocess
import re
from datetime import datetime

# Clasifica un dispositivo basado en su descripción.
def clasificar_dispositivo(descripcion):
    descripcion_lower = descripcion.lower()
    if any(keyword in descripcion_lower for keyword in ["keyboard", "teclado", "input"]):
        return "Entrada"
    elif any(keyword in descripcion_lower for keyword in ["mouse", "ratón", "pointer"]):
        return "Entrada"
    elif any(keyword in descripcion_lower for keyword in ["audio", "speaker", "headset", "micrófono", "microphone"]):
        return "Audio"
    elif any(keyword in descripcion_lower for keyword in ["camera", "webcam"]):
        return "Camara"
    elif any(keyword in descripcion_lower for keyword in ["usb drive", "storage", "disk", "almacenamiento"]):
        return "Almacenamiento"
    elif any(keyword in descripcion_lower for keyword in ["bluetooth", "wireless"]):
        return "Conectividad"
    else:
        return "Otros"

# Obtiene periféricos en Windows, incluyendo versiones de controladores.
def obtener_perifericos_windows():
    dispositivos = []

    try:
        # Listar todos los dispositivos con Win32_PnPSignedDriver, incluyendo versiones de controladores
        output = subprocess.check_output(["wmic", "path", "Win32_PnPSignedDriver", "get", "DeviceName,DriverVersion"], text=True)
        lineas = output.strip().split("\n")[1:]  # Ignorar encabezado
        for linea in lineas:
            if linea.strip():
                partes = linea.split()
                descripcion = " ".join(partes[:-1]).strip()
                version_controlador = partes[-1].strip()
                
                if descripcion:
                    dispositivos.append({
                        "descripcion": descripcion,
                        "categoria": clasificar_dispositivo(descripcion),
                        "version_controlador": version_controlador
                    })
    except Exception as e:
        print(f"Error al ejecutar comandos en Windows: {e}")

    return dispositivos

# Obtiene periféricos en Linux usando lsusb y lshw.
def obtener_perifericos_linux():
    dispositivos = []

    try:
        # Obtener dispositivos con lsusb
        output_lsusb = subprocess.check_output(["lsusb"], text=True)
        lineas_lsusb = output_lsusb.strip().split("\n")
        for linea in lineas_lsusb:
            descripcion = linea.split(":")[-1].strip()
            dispositivos.append({
                "descripcion": descripcion,
                "categoria": clasificar_dispositivo(descripcion),
                "version_controlador": "No disponible en Linux"
            })

        # Obtener dispositivos con lshw (si está disponible)
        try:
            output_lshw = subprocess.check_output(["lshw", "-C", "input"], text=True)
            lineas_lshw = output_lshw.strip().split("\n")
            for linea in lineas_lshw:
                if "product:" in linea:
                    descripcion = linea.split("product:")[-1].strip()
                    dispositivos.append({
                        "descripcion": descripcion,
                        "categoria": clasificar_dispositivo(descripcion),
                        "version_controlador": "No disponible en Linux"
                    })
        except FileNotFoundError:
            print("El comando 'lshw' no está disponible. Para más información detallada, instala 'lshw'.")

    except FileNotFoundError:
        print("El comando 'lsusb' no está disponible. Asegúrate de tener instalado 'usbutils'.")
    except subprocess.SubprocessError as e:
        print(f"Error al ejecutar comandos en Linux: {e}")

    return dispositivos

# Obtiene periféricos en macOS usando system_profiler SPUSBDataType y SPBluetoothDataType.
def obtener_perifericos_macos():
    dispositivos = []

    try:
        # Obtener dispositivos USB con system_profiler
        output_usb = subprocess.check_output(["system_profiler", "SPUSBDataType"], text=True)
        lineas_usb = output_usb.strip().split("\n")
        for linea in lineas_usb:
            if "Product Name:" in linea:
                descripcion = linea.split(":")[1].strip()
                dispositivos.append({
                    "descripcion": descripcion,
                    "categoria": clasificar_dispositivo(descripcion),
                    "version_controlador": "No disponible en macOS"
                })

        # Obtener dispositivos Bluetooth y otros periféricos
        output_bt = subprocess.check_output(["system_profiler", "SPBluetoothDataType"], text=True)
        lineas_bt = output_bt.strip().split("\n")
        for linea in lineas_bt:
            if "Name:" in linea:
                descripcion = linea.split(":")[1].strip()
                dispositivos.append({
                    "descripcion": descripcion,
                    "categoria": clasificar_dispositivo(descripcion),
                    "version_controlador": "No disponible en macOS"
                })

    except subprocess.SubprocessError as e:
        print(f"Error al ejecutar system_profiler en macOS: {e}")

    return dispositivos

# Función principal que detecta el sistema operativo y obtiene la lista de periféricos externos.
def main():
    sistema_operativo = platform.system()
    dispositivos = []

    if sistema_operativo == "Windows":
        dispositivos = obtener_perifericos_windows()
    elif sistema_operativo == "Linux":
        dispositivos = obtener_perifericos_linux()
    elif sistema_operativo == "Darwin":  # Darwin es el nombre base de macOS
        dispositivos = obtener_perifericos_macos()
    else:
        print("Sistema operativo no soportado.")

    if dispositivos:
        # Crear la carpeta de salida con la fecha actual
        json_folder = f"Archivos-JSON/{datetime.now().strftime('%Y-%m-%d')}"
        if not os.path.exists(json_folder):
            os.makedirs(json_folder)
        
        # Guardar el archivo JSON en la carpeta correspondiente
        filepath = os.path.join(json_folder, "Perifericos.json")
        with open(filepath, "w", encoding="utf-8") as archivo:
            json.dump(dispositivos, archivo, indent=4, ensure_ascii=False)
        print(f"Archivo '{filepath}' generado exitosamente con los periféricos.")
    else:
        print("No se encontraron periféricos conectados.")

if __name__ == "__main__":
    main()
