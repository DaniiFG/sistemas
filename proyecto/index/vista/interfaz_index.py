class InterfazIndex:
    def __init__(self):
        pass
    
    def mostrar_inicio(self):
        print("=== INDEXADOR INICIADO ===")
        print("Esperando conexiones de nodos...")
        print("Puerto: 8080")
    
    def mostrar_nodo_conectado(self, nombre, ip):
        print(f"Nodo conectado: {nombre} desde {ip}")
    
    def mostrar_nodos_registrados(self, nodos):
        print("Nodos registrados:")
        for nodo in nodos:
            print(f"  - {nodo['nombre']} ({nodo['ip']})")
    
    def mostrar_numeros_enviados(self, nombre, numeros):
        print(f"Números enviados a {nombre}: {numeros}")
    
    def mostrar_lista_actualizada(self, nombre):
        print(f"Lista de nodos actualizada enviada a {nombre}")