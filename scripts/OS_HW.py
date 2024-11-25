import platform
import json
import os
import subprocess
import re
from datetime import datetime

def execute_command(command, description=""):
    # Ejecuta un comando en la terminal y maneja posibles errores.
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if result.returncode != 0:
            raise RuntimeError(f"Error en '{description}': {result.stderr.strip()}")
        return result.stdout.strip()
    except subprocess.SubprocessError as e:
        return f"Error de ejecución en '{description}': {str(e)}"
    except Exception as e:
        return f"Error general en '{description}': {str(e)}"

def command_exists(command):
    # Verifica si un comando está disponible en el sistema.
    return subprocess.run(f"command -v {command}", shell=True, stdout=subprocess.PIPE).returncode == 0

def get_system_info():
    # Recopila información básica del sistema operativo.
    if platform.system() == "Darwin":
        if not command_exists("sw_vers"):
            return {"Error": "Comando sw_vers no disponible en macOS"}
        cmd = "sw_vers"
        output = execute_command(cmd, description="información del sistema en macOS")
        return {
            "Nombre del Sistema Operativo": "macOS",
            "Detalles": output
        }
    return {
        "Nombre del Sistema Operativo": platform.system(),
        "Versión del Sistema Operativo": platform.version(),
        "Arquitectura": platform.architecture()[0],
    }

def get_cpu_info():
    # Recopila información detallada del procesador (CPU) para macOS, Windows y Linux.
    cpu_info = {}

    if platform.system() == "Darwin":
        if not command_exists("sysctl"):
            return {"Error": "Comando sysctl no disponible en macOS"}
        cmd = "sysctl -n machdep.cpu.brand_string"
        output = execute_command(cmd, description="información de la CPU en macOS")
        cpu_info["Modelo de CPU"] = output

    elif platform.system() == "Windows":
        cmd = "wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed /format:list"
        output = execute_command(cmd, description="información de la CPU en Windows")
        for line in output.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                cpu_info[key.strip()] = value.strip()

    else:
        if not command_exists("lscpu"):
            return {"Error": "Comando lscpu no disponible"}
        cmd = "lscpu | grep -E 'Model name|^CPU\(s\)|Thread|MHz'"
        output = execute_command(cmd, description="información de la CPU en Linux")
        for line in output.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                cpu_info[key.strip()] = value.strip()

    return cpu_info or {"Error": "No se pudo obtener información de la CPU"}

def get_gpu_info():
    # Recopila información detallada de las tarjetas gráficas (GPUs) para macOS, Windows y Linux.
    gpu_info = []

    if platform.system() == "Darwin":
        if not command_exists("system_profiler"):
            return [{"Error": "Comando system_profiler no disponible en macOS"}]
        cmd = "system_profiler SPDisplaysDataType"
        output = execute_command(cmd, description="información de la GPU en macOS")
        gpu = {}
        for line in output.splitlines():
            if "Chipset Model:" in line:
                gpu["Nombre"] = line.split(":")[1].strip()
            elif "VRAM (Total):" in line or "VRAM (Dynamic, Max):" in line:
                gpu["Memoria Dedicada (MB)"] = line.split(":")[1].strip()
            if len(gpu) > 0:
                gpu_info.append(gpu)
        return gpu_info or [{"Error": "No se pudo obtener información de la GPU"}]

    elif platform.system() == "Windows":
        cmd = "wmic path win32_videocontroller get Name,AdapterRAM,DriverVersion /format:list"
        output = execute_command(cmd, description="listado de GPUs en Windows")
        gpu = {}
        for line in output.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip()
                if key == "Name":
                    gpu["Nombre"] = value
                elif key == "AdapterRAM":
                    try:
                        gpu["Memoria Dedicada (MB)"] = round(int(value) / (1024 ** 2), 2)
                    except ValueError:
                        gpu["Memoria Dedicada (MB)"] = "No disponible"
                elif key == "DriverVersion":
                    gpu["Versión del Controlador"] = value
                if len(gpu) == 3:
                    gpu_info.append(gpu)
                    gpu = {}
        if gpu:
            gpu_info.append(gpu)

    else:
        if not command_exists("lspci"):
            return [{"Error": "Comando lspci no disponible"}]
        cmd_lspci = "lspci | grep -i vga"
        output_lspci = execute_command(cmd_lspci, description="listado de GPUs en Linux")
        output_nvidia = None
        if any("NVIDIA" in line for line in output_lspci.splitlines()) and command_exists("nvidia-smi"):
            cmd_nvidia = "nvidia-smi --query-gpu=driver_version,memory.total --format=csv,noheader"
            output_nvidia = execute_command(cmd_nvidia, description="información de la GPU NVIDIA en Linux")
            output_nvidia_lines = output_nvidia.splitlines()
        for index, line in enumerate(output_lspci.splitlines()):
            gpu = {
                "Nombre": line.split(":")[-1].strip(),
                "Memoria Dedicada (MB)": output_nvidia_lines[index].split(',')[1].strip() if output_nvidia and "NVIDIA" in line else "Desconocida",
                "Versión del Controlador": output_nvidia_lines[index].split(',')[0].strip() if output_nvidia and "NVIDIA" in line else "Desconocida"
            }
            gpu_info.append(gpu)

    return gpu_info or [{"Error": "No se pudo obtener información de las GPUs"}]

def get_memory_info():
    # Recopila información detallada de la memoria RAM para macOS, Windows y Linux.
    memory_info = []

    if platform.system() == "Darwin":
        if not command_exists("system_profiler"):
            return [{"Error": "Comando system_profiler no disponible en macOS"}]
        cmd = "system_profiler SPMemoryDataType"
        output = execute_command(cmd, description="información de la RAM en macOS")
        module = {}
        for line in output.splitlines():
            if "Size:" in line:
                module["Capacidad (GB)"] = line.split(":")[1].strip()
            elif "Speed:" in line:
                module["Velocidad (MHz)"] = line.split(":")[1].strip()
            elif "Manufacturer:" in line:
                module["Fabricante"] = line.split(":")[1].strip()
            if len(module) == 3:
                memory_info.append(module)
                module = {}
        return memory_info or [{"Error": "No se pudo obtener información de la RAM"}]

    elif platform.system() == "Windows":
        cmd = "wmic memorychip get Capacity,Speed,Manufacturer /format:list"
        output = execute_command(cmd, description="información de la RAM en Windows")
        module = {}
        for line in output.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                if key.strip() == "Capacity":
                    module["Capacidad (GB)"] = round(int(value.strip()) / (1024 ** 3), 2)
                elif key.strip() == "Speed":
                    module["Velocidad (MHz)"] = value.strip()
                elif key.strip() == "Manufacturer":
                    module["Fabricante"] = value.strip()
                if len(module) == 3:
                    memory_info.append(module)
                    module = {}

    else:
        if not command_exists("dmidecode"):
            return [{"Error": "Comando dmidecode no disponible"}]
        cmd = "dmidecode -t memory | grep -E 'Size|Speed|Manufacturer'"
        output = execute_command(cmd, description="información de la RAM en Linux")
        module = {}
        for line in output.splitlines():
            if "Size" in line:
                module["Capacidad (GB)"] = line.split(":")[1].strip()
            elif "Speed" in line:
                module["Velocidad (MHz)"] = line.split(":")[1].strip()
            elif "Manufacturer" in line:
                module["Fabricante"] = line.split(":")[1].strip()
            if len(module) == 3:
                memory_info.append(module)
                module = {}

    return memory_info or [{"Error": "No se pudo obtener información de la RAM"}]

def get_storage_info():
    # Recopila información detallada del almacenamiento para macOS, Windows y Linux.
    storage_info = []

    if platform.system() == "Darwin":
        if not command_exists("diskutil"):
            return [{"Error": "Comando diskutil no disponible en macOS"}]
        cmd = "diskutil info -all"
        output = execute_command(cmd, description="información de almacenamiento en macOS")
        storage = {}
        for line in output.splitlines():
            if "Device Identifier:" in line:
                if storage:
                    storage_info.append(storage)
                    storage = {}
                storage["Nombre"] = line.split(":")[1].strip()
            elif "Total Size:" in line:
                storage["Capacidad"] = line.split(":")[1].split("(")[0].strip()
            elif "Device / Media Name:" in line:
                storage["Modelo"] = line.split(":")[1].strip()
            elif "File System Personality:" in line:
                storage["Tipo"] = line.split(":")[1].strip()
        if storage:
            storage_info.append(storage)

    elif platform.system() == "Windows":
        cmd = "wmic diskdrive get caption, size, mediaType, firmwareRevision /format:list"
        output = execute_command(cmd, description="información de almacenamiento en Windows")
        disk = {}
        for line in output.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip()
                if key == "Caption":
                    if disk:
                        storage_info.append(disk)
                        disk = {}
                    disk["Nombre"] = value
                elif key == "Size":
                    disk["Capacidad (GB)"] = round(int(value) / (1024 ** 3), 2)
                elif key == "MediaType":
                    disk["Tipo"] = value
                elif key == "FirmwareRevision":
                    disk["Versión Firmware"] = value
        if disk:
            storage_info.append(disk)

    else:
        if not command_exists("lsblk"):
            return [{"Error": "Comando lsblk no disponible"}]
        cmd = "lsblk -o NAME,SIZE,TYPE,MODEL | grep disk"
        output = execute_command(cmd, description="información de almacenamiento en Linux")
        for line in output.splitlines():
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 4:
                storage_info.append({
                    "Nombre": parts[0],
                    "Capacidad": parts[1],
                    "Tipo": parts[2],
                    "Modelo": " ".join(parts[3:])
                })

    return storage_info or [{"Error": "No se pudo obtener información del almacenamiento"}]

def save_to_json(data, filename="OS_HW.json"):
    # Crear la carpeta de salida con la fecha actual
    json_folder = f"Archivos-JSON/{datetime.now().strftime('%Y-%m-%d')}"
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)
    
    # Guardar el archivo JSON en la carpeta correspondiente
    filepath = os.path.join(json_folder, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as json_file:
            existing_data = json.load(json_file)
        if existing_data == data:
            print(f"Los datos ya están actualizados en {filename}. No se realizaron cambios.")
            return
        print("Los datos han cambiado. Actualizando el archivo...")
    
    with open(filepath, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    print(f"Información guardada en {filepath}")


def main():
    print("=== Recopilación de Información ===")

    # Sistema Operativo
    system_info = get_system_info()
    print("\n=== Información del Sistema Operativo ===")
    print(system_info)

    # Procesador (CPU)
    cpu_info = get_cpu_info()
    print("\n=== Información del Procesador (CPU) ===")
    print(cpu_info)

    # Tarjetas Gráficas (GPU)
    gpu_info = get_gpu_info()
    print("\n=== Información de las Tarjetas Gráficas (GPU) ===")
    print(gpu_info)

    # Memoria RAM
    memory_info = get_memory_info()
    print("\n=== Información de la Memoria RAM ===")
    print(memory_info)

    # Almacenamiento
    storage_info = get_storage_info()
    print("\n=== Información del Almacenamiento ===")
    print(storage_info)

    # Guardar todo
    full_data = {
        "Sistema Operativo": system_info,
        "CPU": cpu_info,
        "GPUs": gpu_info,
        "RAM": memory_info,
        "Almacenamiento": storage_info,
    }
    save_to_json(full_data)

if __name__ == "__main__":
    main()
