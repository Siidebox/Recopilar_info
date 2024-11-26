import platform
import json
import os
import subprocess
import re
from datetime import datetime


# Verifica si un comando está disponible en el sistema.
def command_exists(command):
    if platform.system() == "Windows":
        # En Windows, utilizamos 'where' para verificar la existencia del comando
        result = subprocess.run(
            f"where {command}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    else:
        # En Linux/macOS utilizamos 'command -v'
        result = subprocess.run(
            f"command -v {command}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    return result.returncode == 0


# Ejecuta un escaneo de Nmap sin usar librerías específicas y analiza la salida.
# :param targets: Dirección IP o rango de hosts a escanear.
# :param ports: Rango de puertos a escanear.
# :return: Diccionario con resultados del escaneo.
def execute_nmap_scan(targets, ports):
    scan_results = {}

    # Verifica si Nmap está disponible
    if not command_exists("nmap"):
        print("Nmap no está instalado o no está disponible en el PATH del sistema.")
        return {}

    # Construye el comando Nmap
    command = f"nmap -p {ports} -sV {targets}"
    try:
        # Ejecuta el comando y captura la salida
        print(f"Ejecutando: {command}")
        output = subprocess.getoutput(command)

        # Procesa la salida de Nmap
        current_host = None
        for line in output.splitlines():
            # Detecta un host
            if line.startswith("Nmap scan report for"):
                current_host = line.split()[-1]
                scan_results[current_host] = {"Estado": "Indeterminado", "Puertos": []}
            # Detecta el estado del host
            elif line.startswith("Host is up"):
                if current_host:
                    scan_results[current_host]["Estado"] = "Activo"
            # Detecta los puertos y servicios
            elif re.match(r"\d+/tcp", line) or re.match(r"\d+/udp", line):
                if current_host:
                    port_data = line.split()
                    port_info = {
                        "Puerto": port_data[0].split("/")[0],
                        "Protocolo": port_data[0].split("/")[1],
                        "Estado": port_data[1],
                        "Servicio": port_data[2],
                        "Versión": (
                            " ".join(port_data[3:])
                            if len(port_data) > 3
                            else "Desconocida"
                        ),
                    }
                    scan_results[current_host]["Puertos"].append(port_info)

        # Añadir el comando de escaneo a los resultados
        scan_results["Comando"] = command

    except RuntimeError as e:
        print(
            f"Error al ejecutar Nmap: {str(e)}. Asegúrate de que Nmap esté instalado y que tengas permisos suficientes para ejecutarlo."
        )
    except Exception as e:
        print(f"Error general ejecutando Nmap: {str(e)}")

    return scan_results


# Guarda los resultados del escaneo en un archivo JSON.
# :param data: Datos a guardar.
# :param filename: Nombre del archivo JSON.
def save_to_json(data, filename="Red-scan.json"):
    if not data:
        print("No se encontraron resultados para guardar.")
        return

    # Crear la carpeta de salida con la fecha actual
    json_folder = f"Archivos-JSON/{datetime.now().strftime('%Y-%m-%d')}"
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)

    # Guardar el archivo JSON en la carpeta correspondiente
    filepath = os.path.join(json_folder, filename)
    with open(filepath, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    print(f"Información guardada en '{filepath}'")


def main():
    print("=== Escaneo de Puertos Bien Conocidos (0-1023) ===")

    # Define objetivos y rango de puertos por defecto
    targets = "127.0.0.1"
    ports = "0-1023"

    # Nota sobre permisos
    print(
        "Nota: Es posible que necesites permisos administrativos para ejecutar el escaneo de puertos."
    )

    # Realiza el escaneo
    scan_results = execute_nmap_scan(targets, ports)

    # Muestra los resultados
    for host, info in scan_results.items():
        if host == "Comando":
            continue
        print(f"\nHost: {host}")
        print(f"Estado: {info['Estado']}")
        for port_info in info["Puertos"]:
            print(
                f"  Puerto {port_info['Puerto']}/{port_info['Protocolo']} - {port_info['Estado']}"
            )
            print(
                f"    Servicio: {port_info['Servicio']} - Versión: {port_info['Versión']}"
            )

    # Guarda los resultados
    save_to_json(scan_results)


if __name__ == "__main__":
    main()
