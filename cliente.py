"""
Cliente Interactivo de Sockets - PFO 3 Programación sobre Redes
Se conecta al servidor distribuido para enviar tareas y recibir resultados.
"""

import socket
import json
import time

HOST = 'localhost'
PORT = 5000

class ClienteDistribuido:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port

    def _enviar_peticion(self, peticion_dict):
        """Abre un socket, envía la petición JSON y recibe la respuesta."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(json.dumps(peticion_dict).encode('utf-8'))
                respuesta_raw = s.recv(4096)
                return json.loads(respuesta_raw.decode('utf-8'))
        except ConnectionRefusedError:
            print("Error: No se pudo conectar al servidor. Verifique que 'servidor.py' esté ejecutándose.")
            return None
        except Exception as e:
            print(f"Error en la comunicación por socket: {e}")
            return None

    def enviar_tarea(self):
        print("\n--- ENVIAR NUEVA TAREA AL SERVIDOR ---")
        print("1. Procesar texto (Convertir a mayúsculas)")
        print("2. Resolver cálculo matemático")
        print("3. Tarea genérica")
        op = input("Seleccione el tipo de tarea (1-3): ").strip()

        if op == '1':
            tipo = "procesar_texto"
            datos = input("Ingrese el texto a procesar: ")
        elif op == '2':
            tipo = "calcular"
            datos = input("Ingrese la expresión matemática (ej: 15 * 40 / 2): ")
        else:
            tipo = "generica"
            datos = input("Ingrese el contenido de la tarea: ")

        peticion = {
            "accion": "enviar_tarea",
            "tipo": tipo,
            "datos": datos
        }

        res = self._enviar_peticion(peticion)
        if res and res.get("status") == "OK":
            tarea_id = res.get("tarea_id")
            print(f"✅ {res.get('mensaje')}")
            print(f"📌 Tarea asignada con ID #{tarea_id} (Estado: {res.get('estado')})")
            
            # Opción de consultar resultado inmediatamente tras una breve espera
            esperar = input("¿Desea esperar y consultar el resultado ahora? (s/n): ").strip().lower()
            if esperar == 's':
                print("⏳ Esperando que los workers procesen la tarea...")
                time.sleep(2)
                self.consultar_tarea(tarea_id_param=tarea_id)

    def consultar_tarea(self, tarea_id_param=None):
        if tarea_id_param is None:
            print("\n--- CONSULTAR ESTADO DE TAREA ---")
            inp = input("Ingrese el ID de la tarea a consultar: ").strip()
            if not inp.isdigit():
                print("❌ El ID debe ser un número entero.")
                return
            tarea_id = int(inp)
        else:
            tarea_id = tarea_id_param

        peticion = {
            "accion": "consultar_resultado",
            "tarea_id": tarea_id
        }

        res = self._enviar_peticion(peticion)
        if res:
            info = res.get("info", {})
            estado = info.get("estado")
            if estado == "COMPLETADO":
                print(f"✅ Tarea #{tarea_id} [COMPLETADA]:")
                print(f"   Resultado: {info.get('resultado')}")
                print(f"   Timestamp: {info.get('timestamp')}")
            elif estado == "EN_PROGRESO":
                print(f"⏳ Tarea #{tarea_id} todavía está EN PROGRESO en los workers.")
            else:
                print(f"❌ Tarea #{tarea_id} no fue encontrada en la base de datos.")

    def listar_todas(self):
        print("\n--- LISTADO GENERAL DE TAREAS ---")
        peticion = {"accion": "listar_todas"}
        res = self._enviar_peticion(peticion)

        if res and res.get("status") == "OK":
            tareas = res.get("tareas", {})
            print(f"📋 Total de tareas registradas: {res.get('total')}")
            for tid, info in tareas.items():
                est = info.get("estado")
                res_val = info.get("resultado")
                simbolo = "✔" if est == "COMPLETADO" else "⏳"
                print(f"   ID #{tid} | {simbolo} [{est}] | Resultado: {res_val}")

def main():
    cliente = ClienteDistribuido()
    while True:
        print("\n==========================================")
        print("   CLIENTE DISTRIBUIDO (SOCKETS TCP) - PFO3")
        print("==========================================")
        print("1. Enviar nueva tarea (POST por socket)")
        print("2. Consultar resultado de tarea por ID")
        print("3. Listar todas las tareas")
        print("0. Salir")
        print("------------------------------------------")

        opcion = input("Seleccione una opción (0-3): ").strip()

        if opcion == '1':
            cliente.enviar_tarea()
        elif opcion == '2':
            cliente.consultar_tarea()
        elif opcion == '3':
            cliente.listar_todas()
        elif opcion == '0':
            print("Gracias por utilizar el cliente de la PFO3!")
            break
        else:
            print("❌ Opción inválida. Intente de nuevo.")

if __name__ == '__main__':
    main()
