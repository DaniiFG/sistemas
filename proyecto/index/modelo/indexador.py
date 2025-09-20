import socket
import random
import threading

class SocketServidor:
    def __init__(self, host, puerto):
        self.host = host
        self.puerto = puerto
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def bind_listen(self):
        self.socket.bind((self.host, self.puerto))
        self.socket.listen(5)
    
    def accept_connection(self):
        return self.socket.accept()
    
    def close(self):
        self.socket.close()

class GeneradorNumeros:
    @staticmethod
    def generar_listas_exactas():
        """
        Genera 5 listas que contienen EXACTAMENTE 5 copias de cada número 0-10
        Total: 55 números (11 números x 5 copias), distribuidos en 5 listas de 11 números
        """
        # Crear pool con EXACTAMENTE 5 copias de cada número 0-10
        pool_total = []
        for numero in range(11):  # 0 a 10
            pool_total.extend([numero] * 5)
        
        print(f"Pool total creado: {len(pool_total)} números")
        
        # Verificar el pool
        conteo_pool = {}
        for num in pool_total:
            conteo_pool[num] = conteo_pool.get(num, 0) + 1
        
        print("Conteo en pool:")
        for i in range(11):
            print(f"  {i}: {conteo_pool.get(i, 0)} veces")
        
        # Mezclar aleatoriamente
        random.shuffle(pool_total)
        
        # Distribuir en 5 listas de 11 números cada una
        listas = []
        for i in range(5):
            inicio = i * 11
            fin = inicio + 11
            lista = pool_total[inicio:fin]
            listas.append(lista)
        
        return listas

class Indexador:
    def __init__(self):
        self.nodos_registrados = []
        self.socket_servidor = SocketServidor('0.0.0.0', 8080)
        self.generador = GeneradorNumeros()
        self.listas_predefinidas = self.generador.generar_listas_exactas()
        self.contador_nodos = 0
        # Debug: mostrar las listas generadas
        print("=== LISTAS GENERADAS PARA DISTRIBUCIÓN ===")
        for i, lista in enumerate(self.listas_predefinidas):
            print(f"Lista {i+1}: {sorted(lista)}")
        self.verificar_distribucion()
    
    def verificar_distribucion(self):
        """Verifica que la distribución sea exacta"""
        print("=== VERIFICACIÓN DE DISTRIBUCIÓN ===")
        conteo_total = {}
        for numero in range(11):
            conteo_total[numero] = 0
        
        for lista in self.listas_predefinidas:
            for num in lista:
                if 0 <= num <= 10:
                    conteo_total[num] += 1
        
        print("Disponibilidad de cada número:")
        todos_exactos = True
        for numero in range(11):
            count = conteo_total[numero]
            status = "✅" if count == 5 else "❌"
            print(f"  Número {numero}: {count} veces {status}")
            if count != 5:
                todos_exactos = False
        
        if todos_exactos:
            print("✅ PERFECTO: Todos los números aparecen exactamente 5 veces")
        else:
            print("❌ ERROR: Distribución no es exacta")
    
    def registrar_nodo(self, nombre, ip):
        nodo_info = {'nombre': nombre, 'ip': ip}
        self.nodos_registrados.append(nodo_info)
        return self.nodos_registrados.copy()
    
    def generar_numeros_para_nodo(self):
        if self.contador_nodos < len(self.listas_predefinidas):
            numeros = self.listas_predefinidas[self.contador_nodos]
            self.contador_nodos += 1
            return numeros
        else:
            print("❌ ERROR: Más nodos de los esperados")
            return [random.randint(0, 10) for _ in range(11)]
    
    def obtener_nodos_registrados(self):
        return self.nodos_registrados
    
    def iniciar_servidor(self):
        self.socket_servidor.bind_listen()
        return self.socket_servidor