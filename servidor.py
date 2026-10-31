"""
Servidor Distribuido de Tareas (Sockets + ThreadPool Workers)
PFO 3 - Programación sobre Redes
"""

import socket
import threading
import json
import time
import queue
from concurrent.futures import ThreadPoolExecutor

# Configuración del Servidor
HOST = 'localhost'
PORT = 5000
MAX_WORKERS = 4  # Pool de hilos para procesar tareas concurrentemente

# Cola de tareas distribuida (simula el comportamiento de una cola RabbitMQ)
cola_tareas = queue.Queue()
# Almacenamiento distribuido simulado para resultados (PostgreSQL / S3)
resultados_db = {}
resultados_lock = threading.Lock()

def procesar_tarea_worker(tarea_id, tipo_tarea, datos):
    """
    Función que ejecuta cada Worker en su hilo del ThreadPoolExecutor.
    Simula el procesamiento asíncrono o distribuido de la tarea.
    """
    print(f"  [Worker {threading.current_thread().name}] Procesando Tarea #{tarea_id} ({tipo_tarea})...")
    time.sleep(1.5)  # Simula trabajo intensivo I/O o CPU
    
    # Lógica según el tipo de tarea
    if tipo_tarea == "procesar_texto":
        resultado = datos.upper()
    elif tipo_tarea == "calcular":
        try:
            resultado = eval(datos)
        except Exception as e:
            resultado = f"Error en cálculo: {str(e)}"
    else:
        resultado = f"Procesado: {datos}"

    # Guardar el resultado en la 'DB/S3' con sincronización
    with resultados_lock:
        resultados_db[tarea_id] = {
            "estado": "COMPLETADO",
            "resultado": resultado,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    print(f"  [Worker {threading.current_thread().name}] Tarea #{tarea_id} finalizada exitosamente.")
    return resultado

def manejador_cliente(conn, addr, executor):
    """
    Atiende la conexión del socket de un cliente.
    Recibe la solicitud JSON, asigna la tarea al pool de workers y responde.
    """
    print(f"[+] Nueva conexión establecida desde {addr}")
    try:
        while True:
            datos_raw = conn.recv(4096)
            if not datos_raw:
                break
            
            peticion = json.loads(datos_raw.decode('utf-8'))
            accion = peticion.get('accion')

            if accion == 'enviar_tarea':
                tarea_id = len(resultados_db) + 1
                tipo = peticion.get('tipo', 'general')
                contenido = peticion.get('datos', '')

                # Registrar estado inicial
                with resultados_lock:
                    resultados_db[tarea_id] = {"estado": "EN_PROGRESO", "resultado": None}

                # Enviar tarea al Pool de Workers
                executor.submit(procesar_tarea_worker, tarea_id, tipo, contenido)

                respuesta = {
                    "status": "OK",
                    "mensaje": "Tarea recibida y distribuida a los workers.",
                    "tarea_id": tarea_id,
                    "estado": "EN_PROGRESO"
                }

            elif accion == 'consultar_resultado':
                tarea_id = peticion.get('tarea_id')
                with resultados_lock:
                    info = resultados_db.get(tarea_id, {"estado": "NO_ENCONTRADA", "resultado": None})
                
                respuesta = {
                    "status": "OK" if info["estado"] != "NO_ENCONTRADA" else "ERROR",
                    "tarea_id": tarea_id,
                    "info": info
                }

            elif accion == 'listar_todas':
                with resultados_lock:
                    copia_db = dict(resultados_db)
                respuesta = {
                    "status": "OK",
                    "total": len(copia_db),
                    "tareas": copia_db
                }

            else:
                respuesta = {"status": "ERROR", "mensaje": "Acción no reconocida."}

            # Enviar respuesta JSON al cliente por socket
            conn.sendall(json.dumps(respuesta).encode('utf-8'))

    except Exception as e:
        print(f"[-] Error gestionando cliente {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Conexión cerrada con {addr}")

def iniciar_servidor():
    # Inicializar el Pool de Workers (ThreadPoolExecutor)
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="WorkerThread")
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Reusar dirección para evitar el error 'Address already in use'
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print("=====================================================")
    print(f" Servidor Distribuido escuchando en {HOST}:{PORT}")
    print(f" Pool de Workers activo con {MAX_WORKERS} hilos concurrentes")
    print("=====================================================")

    try:
        while True:
            conn, addr = server_socket.accept()
            # Crear un hilo para atender cada conexión de cliente sin bloquear
            hilo_cliente = threading.Thread(target=manejador_cliente, args=(conn, addr, executor))
            hilo_cliente.daemon = True
            hilo_cliente.start()
    except KeyboardInterrupt:
        print("\n[!] Apagando el servidor...")
    finally:
        server_socket.close()
        executor.shutdown(wait=False)

if __name__ == '__main__':
    iniciar_servidor()
