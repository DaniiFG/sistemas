class InterfazNodo:
    def __init__(self):
        pass
    
    def mostrar_inicio(self, nombre):
        print(f"=== NODO {nombre} INICIADO ===")
    
    def mostrar_conexion_index(self):
        print("Conectando al indexador...")
    
    def mostrar_numeros_recibidos(self, numeros):
        print(f"Números recibidos del indexador: {numeros}")
    
    def mostrar_otros_nodos(self, nodos):
        print("Otros nodos en la red:")
        for nodo in nodos:
            print(f"  - {nodo['nombre']} ({nodo['ip']})")
    
    def mostrar_inicio_negociacion(self):
        print("Iniciando servidor de negociación...")
        print("Comenzando negociación con otros nodos...")
    
    def mostrar_estado_numeros(self, numeros, repetidos, faltantes):
        print(f"Estado actual: {sorted(numeros)}")
        if repetidos:
            print(f"Números repetidos: {repetidos}")
        if faltantes:
            print(f"Números faltantes: {faltantes}")
    
    def mostrar_intercambio(self, con_quien, di, recibi):
        print(f"Intercambio con {con_quien}: Di {di}, Recibí {recibi}")
    
    def mostrar_coleccion_completa(self):
        print("¡COLECCIÓN COMPLETA! Números del 0 al 10 conseguidos.")
    
    def mostrar_negociacion_con(self, nombre_nodo):
        print(f"Negociando con {nombre_nodo}...")
    
    def mostrar_sin_intercambio(self, nombre_nodo):
        print(f"Sin intercambio posible con {nombre_nodo}")
    
    def mostrar_debug_intercambio(self, nombre_otro, mis_repetidos, mis_faltantes, otros_repetidos, otros_faltantes):
        print(f"  DEBUG - {nombre_otro}:")
        print(f"    Mis repetidos: {mis_repetidos}, Mis faltantes: {mis_faltantes}")
        print(f"    Otros repetidos: {otros_repetidos}, Otros faltantes: {otros_faltantes}")
        
        # Mostrar posibles intercambios
        for mi_rep in mis_repetidos:
            if mi_rep in otros_faltantes:
                for otro_rep in otros_repetidos:
                    if otro_rep in mis_faltantes:
                        print(f"    ✅ POSIBLE: Yo doy {mi_rep} (otros necesitan), recibo {otro_rep} (yo necesito)")
                        return
        print(f"    ❌ Sin intercambio mutuo beneficioso")