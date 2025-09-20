import threading
import time
import json

class ControladorNodo:
    def __init__(self, modelo, vista):
        self.modelo = modelo
        self.vista = vista
    
    def iniciar_sistema(self):
        self.vista.mostrar_inicio(self.modelo.nombre)
        
        # Conectar al indexador
        self.vista.mostrar_conexion_index()
        if not self.modelo.conectar_a_index():
            print("Error: No se pudo conectar al indexador")
            return
        
        self.vista.mostrar_numeros_recibidos(self.modelo.numeros)
        self.vista.mostrar_otros_nodos(self.modelo.otros_nodos)
        
        # Iniciar servidor de negociación
        self.vista.mostrar_inicio_negociacion()
        servidor = self.modelo.iniciar_servidor_negociacion()
        thread_servidor = threading.Thread(target=self.manejar_servidor_negociacion, args=(servidor,))
        thread_servidor.daemon = True
        thread_servidor.start()   # <-- importante: llamar start()

        time.sleep(5)

        
        # Iniciar negociación
        self.iniciar_negociacion()
    
    def manejar_servidor_negociacion(self, servidor):
        # SERVIDOR siempre activo para que los nodos completados sigan ayudando
        while True:
            try:
                conexion, direccion = servidor.accept_connection()
                thread = threading.Thread(target=self.procesar_negociacion_entrante, args=(conexion,))
                thread.daemon = True
                thread.start()
            except Exception as e:
                # log y pequeño sleep para evitar bucle caliente
                print(f"[SERVIDOR] error accept: {e}")
                time.sleep(0.5)

    
    def procesar_negociacion_entrante(self, conexion):
        try:
            data = conexion.recv(1024).decode()
            mensaje = json.loads(data)
            
            if mensaje['tipo'] == 'negociacion':
                nombre_otro = mensaje['nombre']
                numeros_otros = mensaje['numeros']
                repetidos_otros = mensaje['repetidos']
                
                print(f"  [SERVIDOR] Recibida negociación de {nombre_otro}")
                
                # Encontrar intercambio posible
                puedo_dar, puedo_recibir = self.modelo.encontrar_intercambio_posible(numeros_otros, repetidos_otros)
                
                if puedo_dar is not None and puedo_recibir is not None:
                    # Realizar intercambio
                    if self.modelo.realizar_intercambio_especifico(puedo_dar, puedo_recibir):
                        print(f"  [SERVIDOR] ✅ Intercambio realizado con {nombre_otro}: Di {puedo_dar}, Recibí {puedo_recibir}")
                        respuesta = {
                            'acepta_intercambio': True, 
                            'te_doy': puedo_dar, 
                            'necesito': puedo_recibir
                        }
                    else:
                        print(f"  [SERVIDOR] ❌ Error realizando intercambio con {nombre_otro}")
                        respuesta = {'acepta_intercambio': False}
                else:
                    print(f"  [SERVIDOR] ❌ Sin intercambio posible con {nombre_otro}")
                    respuesta = {'acepta_intercambio': False}
                
                conexion.send(json.dumps(respuesta).encode())
                
        except Exception as e:
            print(f"  [SERVIDOR] Error: {e}")
        finally:
            conexion.close()
    
    def iniciar_negociacion(self):
        intentos = 0
        max_intentos = 50  # Más intentos
        
        while not self.modelo.verificar_coleccion_completa() and intentos < max_intentos:
            repetidos = self.modelo.obtener_numeros_repetidos()
            faltantes = self.modelo.obtener_numeros_faltantes()
            
            self.vista.mostrar_estado_numeros(self.modelo.numeros, repetidos, faltantes)
            
            if not repetidos:
                if not faltantes:
                    break
                print("  No tengo números repetidos para intercambiar")
                time.sleep(3)
                intentos += 1
                continue
            
            if not faltantes:
                print("  ¡Colección completa!")
                break
            
            # Intentar negociar con TODOS los nodos
            print(f"\n--- RONDA DE NEGOCIACIÓN {intentos + 1} ---")
            intercambio_realizado = False
            
            for nodo in self.modelo.otros_nodos:
                if self.modelo.verificar_coleccion_completa():
                    break
                
                print(f"\n🔄 Negociando con {nodo['nombre']}...")
                
                # Determinar puerto del otro nodo
                puerto_otro = self.obtener_puerto_por_nombre(nodo['nombre'])
                
                exitoso, di, recibi = self.modelo.negociar_con_nodo(nodo['ip'], puerto_otro)
                
                if exitoso and di and recibi:
                    print(f"✅ ÉXITO: Intercambio con {nodo['nombre']}: Di {di}, Recibí {recibi}")
                    intercambio_realizado = True
                    time.sleep(1)  # Pausa después del intercambio exitoso
                else:
                    print(f"❌ Sin intercambio con {nodo['nombre']}")
            
            if not intercambio_realizado:
                print("  ⏳ Sin intercambios en esta ronda, esperando...")
                time.sleep(2)
                
            intentos += 1
        
        if self.modelo.verificar_coleccion_completa():
            self.vista.mostrar_coleccion_completa()
            final_numeros = sorted(self.modelo.numeros)
            print(f"🎉 COLECCIÓN FINAL: {final_numeros}")
            
            # SEGUIR ESCUCHANDO PARA AYUDAR A OTROS NODOS
            print("🔄 Colección completa, pero sigo ayudando a otros nodos...")
            while True:
                time.sleep(5)
                print("  ⏳ Esperando ayudar a otros nodos...")
        else:
            print(f"❌ No se pudo completar después de {max_intentos} intentos")
            print(f"Estado final: {sorted(self.modelo.numeros)}")
            
            # SEGUIR INTENTANDO INDEFINIDAMENTE
            print("🔄 Continuando intentos indefinidamente...")
            while True:
                time.sleep(5)
                # Intentar una vez más con cada nodo
                for nodo in self.modelo.otros_nodos:
                    if self.modelo.verificar_coleccion_completa():
                        break
                    puerto_otro = self.obtener_puerto_por_nombre(nodo['nombre'])
                    exitoso, di, recibi = self.modelo.negociar_con_nodo(nodo['ip'], puerto_otro)
                    if exitoso:
                        print(f"✅ Intercambio tardío con {nodo['nombre']}: Di {di}, Recibí {recibi}")
                        break
    
    def obtener_puerto_por_nombre(self, nombre):
        puertos = {
            'nodo1': 8081,
            'nodo2': 8082,
            'nodo3': 8083,
            'nodo4': 8084,
            'nodo5': 8085
        }
        return puertos.get(nombre, 8081)