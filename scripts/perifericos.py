import platform
import json
import os
import subprocess
from datetime import datetime

# Verifica si un comando está disponible en el sistema.
def comando_disponible(command):
    return subprocess.run(f"command -v {command}", shell=True, stdout=subprocess.PIPE).returncode == 0

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

# Obtiene periféricos en Linux usando lsusb y lshw.
def obtener_perifericos_linux():
    dispositivos = []

    # Verifica si lsusb está disponible
    if comando_disponible("lsusb"):
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
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar 'lsusb': {e}. Puede que no haya dispositivos conectados o el comando haya fallado.")
    else:
        print("Advertencia: 'lsusb' no está instalado. No se pueden obtener dispositivos USB.")

    # Verifica si lshw está disponible
    if comando_disponible("lshw"):
        try:
            # Obtener dispositivos con lshw (si está disponible)
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
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar 'lshw': {e}")
    else:
        print("Advertencia: 'lshw' no está instalado. No se pueden obtener dispositivos adicionales.")

    return dispositivos

# Función principal que detecta el sistema operativo y obtiene la lista de periféricos externos.
def main():
    sistema_operativo = platform.system()
    dispositivos = []

    if sistema_operativo == "Windows":
        # Implementa la función obtener_perifericos_windows() si es necesario
        pass
    elif sistema_operativo == "Linux":
        dispositivos = obtener_perifericos_linux()
    elif sistema_operativo == "Darwin":  # Darwin es el nombre base de macOS
        # Implementa la función obtener_perifericos_macos() si es necesario
        pass
    else:
        print("Sistema operativo no soportado.")

    # Crear la carpeta de salida con la fecha actual
    json_folder = f"Archivos-JSON/{datetime.now().strftime('%Y-%m-%d')}"
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)

    # Guardar el archivo JSON en la carpeta correspondiente, incluso si está vacío
    filepath = os.path.join(json_folder, "Perifericos.json")
    with open(filepath, "w", encoding="utf-8") as archivo:
        json.dump(dispositivos, archivo, indent=4, ensure_ascii=False)

    if dispositivos:
        print(f"Archivo '{filepath}' generado exitosamente con los periféricos.")
    else:
        print("No se encontraron periféricos conectados. Se ha creado un archivo vacío.")

if __name__ == "__main__":
    main()
