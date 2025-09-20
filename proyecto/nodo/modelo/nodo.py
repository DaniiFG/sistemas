# proyecto/nodo/modelo/nodo.py
import socket
import json
import threading
import time
import random

class SocketCliente:
    def __init__(self):
        self.socket = None
    
    def crear_conexion(self, host, puerto, timeout=5):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(timeout)
        self.socket.connect((host, puerto))
    
    def enviar_datos(self, datos):
        mensaje = json.dumps(datos)
        self.socket.send(mensaje.encode())
    
    def recibir_datos(self):
        data = self.socket.recv(4096).decode()
        return json.loads(data)
    
    def cerrar(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

class SocketServidor:
    def __init__(self, host, puerto):
        self.host = host
        self.puerto = puerto
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def bind_listen(self):
        self.socket.bind((self.host, self.puerto))
        self.socket.listen(10)
    
    def accept_connection(self):
        return self.socket.accept()
    
    def close(self):
        try:
            self.socket.close()
        except:
            pass

class Nodo:
    def __init__(self, nombre, puerto_servidor):
        self.nombre = nombre
        self.puerto_servidor = puerto_servidor
        self.numeros = []
        self.otros_nodos = []
        self.socket_cliente = SocketCliente()
        self.socket_servidor = SocketServidor('0.0.0.0', puerto_servidor)
        self.coleccion_completa = False
        self.lock = threading.Lock()    # <- lock para proteger self.numeros
    
    def conectar_a_index(self):
        try:
            self.socket_cliente.crear_conexion('index', 8080)
            mensaje = {'nombre': self.nombre, 'puerto': self.puerto_servidor}
            self.socket_cliente.enviar_datos(mensaje)
            
            respuesta = self.socket_cliente.recibir_datos()
            # snapshot seguro
            with self.lock:
                self.numeros = respuesta['numeros']
            self.otros_nodos = [nodo for nodo in respuesta['nodos'] if nodo['nombre'] != self.nombre]
            
            self.socket_cliente.cerrar()
            return True
        except Exception as e:
            print(f"Error conectando al index: {e}")
            return False
    
    def verificar_coleccion_completa(self):
        with self.lock:
            numeros_unicos = set(self.numeros)
        self.coleccion_completa = (len(numeros_unicos) == 11 and all(i in numeros_unicos for i in range(11)))
        return self.coleccion_completa
    
    def obtener_numeros_repetidos(self):
        with self.lock:
            conteo = {}
            for num in self.numeros:
                conteo[num] = conteo.get(num, 0) + 1
            repetidos = [num for num, count in conteo.items() if count > 1]
        return repetidos
    
    def obtener_numeros_faltantes(self):
        with self.lock:
            current = set(self.numeros)
        return [i for i in range(11) if i not in current]
    
    def encontrar_intercambio_posible(self, numeros_otros, numeros_repetidos_otros):
        """LÓGICA: múltiples estrategias, devuelve (dar, recibir) o (None, None)"""
        mis_repetidos = self.obtener_numeros_repetidos()
        mis_faltantes = self.obtener_numeros_faltantes()
        
        # Calcular qué le falta al otro
        otros_faltantes = [i for i in range(11) if i not in numeros_otros]
        
        # CASO ESPECIAL: Si YA COMPLETÉ MI COLECCIÓN, puedo dar para ayudar
        if self.verificar_coleccion_completa() and otros_faltantes and numeros_repetidos_otros:
            for numero_que_necesita in otros_faltantes:
                with self.lock:
                    if numero_que_necesita in self.numeros:
                        numero_que_recibo = numeros_repetidos_otros[0]
                        return numero_que_necesita, numero_que_recibo
        
        # ESTRATEGIA 1: intercambio perfecto mutuo
        for mi_repetido in mis_repetidos:
            if mi_repetido in otros_faltantes:
                for otro_repetido in numeros_repetidos_otros:
                    if otro_repetido in mis_faltantes:
                        return mi_repetido, otro_repetido
        
        # ESTRATEGIA 2: doy algo que el otro necesita, recibo cualquier repetido suyo
        for mi_repetido in mis_repetidos:
            if mi_repetido in otros_faltantes and numeros_repetidos_otros:
                otro_repetido = numeros_repetidos_otros[0]
                return mi_repetido, otro_repetido
        
        # ESTRATEGIA 3: recibo algo que necesito (si el otro tiene algo que me falta)
        for otro_repetido in numeros_repetidos_otros:
            if otro_repetido in mis_faltantes and mis_repetidos:
                mi_repetido = mis_repetidos[0]
                return mi_repetido, otro_repetido
        
        return None, None
    
    def realizar_intercambio_especifico(self, dar, recibir):
        """Realiza un intercambio (protegido por lock)"""
        with self.lock:
            if dar in self.numeros:
                # eliminar solo una copia
                self.numeros.remove(dar)
                self.numeros.append(recibir)
                return True
        return False
    
    def iniciar_servidor_negociacion(self):
        self.socket_servidor.bind_listen()
        return self.socket_servidor
    
    def negociar_con_nodo(self, nodo):
        """
        Intenta negociar con otro nodo:
        1. Intercambio directo (mi repetido ↔ tu faltante, tu repetido ↔ mi faltante).
        2. Si no es posible, donación (te paso un repetido mío que te falta aunque yo no reciba nada).
        """

        try:
            # Repetidos y faltantes locales
            repetidos_mios = self.obtener_repetidos()
            faltantes_mios = self.obtener_faltantes()

            # Pedir estado al nodo remoto
            estado_otro = self.pedir_estado(nodo)
            repetidos_otro = estado_otro.get("repetidos", [])
            faltantes_otro = estado_otro.get("faltantes", [])

            # === Paso 1: Intercambio directo ===
            for num_mio in repetidos_mios:
                if num_mio in faltantes_otro:
                    for num_otro in repetidos_otro:
                        if num_otro in faltantes_mios:
                            print(f"[{self.nombre}] Intercambio con {nodo}: doy {num_mio}, recibo {num_otro}")
                            self.intercambiar(nodo, num_mio, num_otro)
                            return True

            # === Paso 2: Donación ===
            for num_mio in repetidos_mios:
                if num_mio in faltantes_otro:
                    print(f"[{self.nombre}] Donación a {nodo}: doy {num_mio}")
                    self.donar(nodo, num_mio)
                    return True

            return False

        except Exception as e:
            print(f"[{self.nombre}] Error negociando con {nodo}: {e}")
            return False


    def donar(self, nodo, num):
        """
        Envía un número repetido a otro nodo sin esperar nada a cambio.
        """

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((nodo["ip"], nodo["puerto"]))

            mensaje = {
                "accion": "donacion",
                "numero": num,
                "origen": self.nombre
            }

            sock.sendall(json.dumps(mensaje).encode("utf-8"))
            sock.close()

            # Actualizar mi lista local
            with self.lock:
                if num in self.numeros:
                    self.numeros.remove(num)

            print(f"[{self.nombre}] Donación enviada: {num} a {nodo['nombre']}")

        except Exception as e:
            print(f"[{self.nombre}] Error al donar a {nodo['nombre']}: {e}")

