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
        self.lock = threading.Lock()
    
    def conectar_a_index(self):
        try:
            self.socket_cliente.crear_conexion('index', 8080)
            mensaje = {'nombre': self.nombre, 'puerto': self.puerto_servidor}
            self.socket_cliente.enviar_datos(mensaje)
            
            respuesta = self.socket_cliente.recibir_datos()
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
        if self.verificar_coleccion_completa() and otros_faltantes:
            for numero_que_necesita in otros_faltantes:
                with self.lock:
                    if numero_que_necesita in self.numeros:
                        # Si el otro tiene repetidos, acepto cualquiera
                        if numeros_repetidos_otros:
                            numero_que_recibo = numeros_repetidos_otros[0]
                            return numero_que_necesita, numero_que_recibo
        
        # ESTRATEGIA 1: intercambio perfecto mutuo (win-win)
        for mi_repetido in mis_repetidos:
            if mi_repetido in otros_faltantes:
                for otro_repetido in numeros_repetidos_otros:
                    if otro_repetido in mis_faltantes:
                        return mi_repetido, otro_repetido
        
        # ESTRATEGIA 2: doy un repetido que el otro necesita, recibo cualquier repetido suyo
        for mi_repetido in mis_repetidos:
            if mi_repetido in otros_faltantes and numeros_repetidos_otros:
                # Prefiero recibir algo que me falta
                for otro_repetido in numeros_repetidos_otros:
                    if otro_repetido in mis_faltantes:
                        return mi_repetido, otro_repetido
                # Si no, acepto cualquier repetido
                return mi_repetido, numeros_repetidos_otros[0]
        
        # ESTRATEGIA 3: recibo algo que necesito, doy cualquier repetido
        for otro_repetido in numeros_repetidos_otros:
            if otro_repetido in mis_faltantes and mis_repetidos:
                return mis_repetidos[0], otro_repetido
        
        return None, None
    
    def realizar_intercambio_especifico(self, dar, recibir):
        """Realiza un intercambio (protegido por lock)"""
        with self.lock:
            if dar in self.numeros:
                self.numeros.remove(dar)
                self.numeros.append(recibir)
                return True
        return False
    
    def iniciar_servidor_negociacion(self):
        self.socket_servidor.bind_listen()
        return self.socket_servidor
    
    def negociar_con_nodo(self, ip_nodo, puerto_nodo):
        """
        Cliente: intenta negociar con otro nodo
        Retorna: (exitoso, numero_dado, numero_recibido)
        """
        try:
            # Preparar mi estado actual
            with self.lock:
                mis_numeros = self.numeros.copy()
            
            mis_repetidos = self.obtener_numeros_repetidos()
            mis_faltantes = self.obtener_numeros_faltantes()
            
            # Si no tengo repetidos, no puedo negociar
            if not mis_repetidos:
                return False, None, None
            
            # Crear conexión con el otro nodo
            cliente = SocketCliente()
            cliente.crear_conexion(ip_nodo, puerto_nodo, timeout=3)
            
            # Enviar propuesta de negociación
            mensaje = {
                'tipo': 'negociacion',
                'nombre': self.nombre,
                'numeros': mis_numeros,
                'repetidos': mis_repetidos,
                'faltantes': mis_faltantes
            }
            
            cliente.enviar_datos(mensaje)
            
            # Recibir respuesta
            respuesta = cliente.recibir_datos()
            cliente.cerrar()
            
            if respuesta.get('acepta_intercambio'):
                numero_recibido = respuesta['te_doy']
                numero_dado = respuesta['necesito']
                
                # Verificar que puedo dar lo que piden
                with self.lock:
                    if numero_dado in self.numeros:
                        self.numeros.remove(numero_dado)
                        self.numeros.append(numero_recibido)
                        return True, numero_dado, numero_recibido
                    else:
                        print(f"  ERROR: No tengo el número {numero_dado} que solicitan")
                        return False, None, None
            
            return False, None, None
            
        except socket.timeout:
            print(f"  Timeout conectando con nodo en {ip_nodo}:{puerto_nodo}")
            return False, None, None
        except Exception as e:
            print(f"  Error negociando: {e}")
            return False, None, None