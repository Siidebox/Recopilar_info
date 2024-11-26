import sys
import platform
import json
import os
import subprocess
import re
from datetime import datetime



from scripts.aplicaciones import main as aplicaciones_main
from scripts.OS_HW import main as os_hw_main
from scripts.perifericos import main as perifericos_main
from scripts.red import main as red_main

def main():
    # Crear la carpeta con la fecha actual dentro de 'Archivos-JSON'
    json_folder = f"Archivos-JSON/{datetime.now().strftime('%Y-%m-%d')}"
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)

    # Ejecutar cada script y guardar sus resultados en la carpeta correspondiente
    # Cada script parcial deberá guardar su JSON dentro de 'json_folder'
    os_hw_main()
    red_main()
    aplicaciones_main()
    perifericos_main()

    # Consolidar todos los archivos JSON en un solo archivo
    data = {}
    
    # Leer cada archivo JSON parcial desde la carpeta con la fecha
    json_files = ["OS_HW.json", "Red-scan.json", "aplicaciones.json", "Perifericos.json"]
    for json_file in json_files:
        file_path = os.path.join(json_folder, json_file)
        if not os.path.exists(file_path):
            print(f"Advertencia: El archivo '{json_file}' no se encontró y será omitido.")
            continue

        with open(file_path, 'r', encoding='utf-8') as file:
            key = json_file.split('.')[0].lower()  # Nombre de la clave en el JSON consolidado
            data[key] = json.load(file)


    # Crear la carpeta con la fecha actual y guardar el archivo consolidado dentro
    info_folder = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(info_folder):
        os.makedirs(info_folder)

    consolidated_filename = os.path.join(info_folder, 'informacion_sistema.json')
    with open(consolidated_filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print(f"Archivo consolidado '{consolidated_filename}' generado exitosamente.")

if __name__ == "__main__":
    main()
