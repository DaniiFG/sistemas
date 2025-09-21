import json
import threading

class ControladorIndex:
    def __init__(self, modelo, vista):
        self.modelo = modelo
        self.vista = vista
    
    def iniciar_sistema(self):
        self.vista.mostrar_inicio()
        servidor = self.modelo.iniciar_servidor()
        
        while True:
            try:
                conexion, direccion = servidor.accept_connection()
                thread = threading.Thread(
                    target=self.manejar_cliente, 
                    args=(conexion, direccion)
                )
                thread.daemon = True
                thread.start()
            except Exception as e:
                print(f"Error en servidor: {e}")
                break
    
    def manejar_cliente(self, conexion, direccion):
        try:
            data = conexion.recv(1024).decode()
            mensaje = json.loads(data)
            
            nombre_nodo = mensaje['nombre']
            ip_nodo = direccion[0]
            
            # Registrar nodo
            nodos_actualizados = self.modelo.registrar_nodo(nombre_nodo, ip_nodo)
            self.vista.mostrar_nodo_conectado(nombre_nodo, ip_nodo)
            
            # Generar números para el nodo
            numeros = self.modelo.generar_numeros_para_nodo()
            self.vista.mostrar_numeros_enviados(nombre_nodo, numeros)
            
            # Preparar respuesta
            respuesta = {
                'numeros': numeros,
                'nodos': nodos_actualizados
            }
            
            # Enviar respuesta
            conexion.send(json.dumps(respuesta).encode())
            self.vista.mostrar_lista_actualizada(nombre_nodo)
            self.vista.mostrar_nodos_registrados(nodos_actualizados)
            
        except Exception as e:
            print(f"Error manejando cliente: {e}")
        finally:
            conexion.close()