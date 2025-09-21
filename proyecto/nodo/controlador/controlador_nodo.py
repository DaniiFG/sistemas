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
        thread_servidor.start()

        # Esperar un poco para que todos los nodos estén listos
        time.sleep(3)
        
        # Iniciar negociación activa
        self.iniciar_negociacion()
    
    def manejar_servidor_negociacion(self, servidor):
        """SERVIDOR siempre activo para responder a peticiones de negociación"""
        while True:
            try:
                conexion, direccion = servidor.accept_connection()
                thread = threading.Thread(target=self.procesar_negociacion_entrante, args=(conexion,))
                thread.daemon = True
                thread.start()
            except Exception as e:
                print(f"[SERVIDOR] Error accept: {e}")
                time.sleep(0.5)
    
    def procesar_negociacion_entrante(self, conexion):
        """Procesa una solicitud de negociación entrante"""
        try:
            data = conexion.recv(4096).decode()
            mensaje = json.loads(data)
            
            if mensaje['tipo'] == 'negociacion':
                nombre_otro = mensaje['nombre']
                numeros_otros = mensaje['numeros']
                repetidos_otros = mensaje['repetidos']
                
                print(f"  [SERVIDOR] Recibida negociación de {nombre_otro}")
                print(f"    Sus números: {sorted(numeros_otros)}")
                print(f"    Sus repetidos: {repetidos_otros}")
                
                # Encontrar intercambio posible
                puedo_dar, puedo_recibir = self.modelo.encontrar_intercambio_posible(
                    numeros_otros, repetidos_otros
                )
                
                if puedo_dar is not None and puedo_recibir is not None:
                    # Realizar intercambio
                    if self.modelo.realizar_intercambio_especifico(puedo_dar, puedo_recibir):
                        print(f"  [SERVIDOR] ✅ Intercambio con {nombre_otro}: Di {puedo_dar}, Recibí {puedo_recibir}")
                        respuesta = {
                            'acepta_intercambio': True, 
                            'te_doy': puedo_dar,  # Lo que YO doy (el cliente recibe)
                            'necesito': puedo_recibir  # Lo que YO recibo (el cliente da)
                        }
                    else:
                        print(f"  [SERVIDOR] ❌ Error realizando intercambio con {nombre_otro}")
                        respuesta = {'acepta_intercambio': False}
                else:
                    print(f"  [SERVIDOR] ❌ Sin intercambio posible con {nombre_otro}")
                    respuesta = {'acepta_intercambio': False}
                
                conexion.send(json.dumps(respuesta).encode())
                
        except Exception as e:
            print(f"  [SERVIDOR] Error procesando: {e}")
            try:
                respuesta = {'acepta_intercambio': False}
                conexion.send(json.dumps(respuesta).encode())
            except:
                pass
        finally:
            conexion.close()
    
    def iniciar_negociacion(self):
        """Cliente activo: intenta completar la colección"""
        intentos = 0
        max_intentos = 100
        sin_cambios = 0
        max_sin_cambios = 10
        
        while not self.modelo.verificar_coleccion_completa() and intentos < max_intentos:
            repetidos = self.modelo.obtener_numeros_repetidos()
            faltantes = self.modelo.obtener_numeros_faltantes()
            
            print(f"\n=== RONDA {intentos + 1} ===")
            self.vista.mostrar_estado_numeros(self.modelo.numeros, repetidos, faltantes)
            
            # Si no tengo repetidos pero me faltan números, espero
            if not repetidos and faltantes:
                print("  ⏳ Sin repetidos para intercambiar, esperando...")
                time.sleep(3)
                intentos += 1
                sin_cambios += 1
                if sin_cambios >= max_sin_cambios:
                    print("  ⚠️ Muchas rondas sin cambios, aumentando tiempo de espera")
                    time.sleep(5)
                continue
            
            # Si tengo la colección completa, salir
            if not faltantes:
                break
            
            # Intentar negociar con todos los nodos
            intercambio_realizado = False
            
            # Mezclar el orden de los nodos para variar las negociaciones
            import random
            nodos_mezclados = self.modelo.otros_nodos.copy()
            random.shuffle(nodos_mezclados)
            
            for nodo in nodos_mezclados:
                if self.modelo.verificar_coleccion_completa():
                    break
                
                print(f"\n  🔄 Intentando negociar con {nodo['nombre']}...")
                
                # Determinar puerto del otro nodo
                puerto_otro = self.obtener_puerto_por_nombre(nodo['nombre'])
                
                # Intentar negociar
                exitoso, di, recibi = self.modelo.negociar_con_nodo(nodo['ip'], puerto_otro)
                
                if exitoso and di is not None and recibi is not None:
                    print(f"  ✅ ÉXITO con {nodo['nombre']}: Di {di}, Recibí {recibi}")
                    self.vista.mostrar_intercambio(nodo['nombre'], di, recibi)
                    intercambio_realizado = True
                    sin_cambios = 0
                    # Pequeña pausa después del intercambio exitoso
                    time.sleep(0.5)
                else:
                    print(f"  ❌ Sin intercambio con {nodo['nombre']}")
            
            if not intercambio_realizado:
                print("  ⏳ Sin intercambios en esta ronda")
                sin_cambios += 1
                if sin_cambios >= max_sin_cambios:
                    print("  ⚠️ Muchas rondas sin cambios, esperando más tiempo...")
                    time.sleep(5)
                else:
                    time.sleep(2)
            else:
                # Si hubo intercambio, espera menos
                time.sleep(1)
            
            intentos += 1
        
        # Verificación final
        if self.modelo.verificar_coleccion_completa():
            self.vista.mostrar_coleccion_completa()
            print(f"🎉 COLECCIÓN FINAL: {sorted(self.modelo.numeros)}")
            print("✅ Verificación: Tengo todos los números del 0 al 10")
            
            # Seguir activo para ayudar a otros nodos
            print("\n🤝 Colección completa. Permaneciendo activo para ayudar a otros nodos...")
            while True:
                time.sleep(10)
                print("  ⏳ Servidor activo, ayudando a otros nodos...")
        else:
            print(f"\n❌ No se pudo completar la colección después de {intentos} intentos")
            print(f"Estado final: {sorted(self.modelo.numeros)}")
            repetidos_finales = self.modelo.obtener_numeros_repetidos()
            faltantes_finales = self.modelo.obtener_numeros_faltantes()
            print(f"Repetidos finales: {repetidos_finales}")
            print(f"Faltantes finales: {faltantes_finales}")
            
            # Seguir intentando indefinidamente pero con menos frecuencia
            print("\n🔄 Continuando intentos con menor frecuencia...")
            while True:
                time.sleep(10)
                
                # Revisar si ahora puedo negociar
                repetidos = self.modelo.obtener_numeros_repetidos()
                faltantes = self.modelo.obtener_numeros_faltantes()
                
                if not faltantes:
                    print("\n🎉 ¡COLECCIÓN COMPLETADA TARDÍAMENTE!")
                    print(f"Colección final: {sorted(self.modelo.numeros)}")
                    break
                
                if repetidos:
                    for nodo in self.modelo.otros_nodos:
                        puerto_otro = self.obtener_puerto_por_nombre(nodo['nombre'])
                        exitoso, di, recibi = self.modelo.negociar_con_nodo(nodo['ip'], puerto_otro)
                        if exitoso:
                            print(f"✅ Intercambio tardío con {nodo['nombre']}: Di {di}, Recibí {recibi}")
                            break
    
    def obtener_puerto_por_nombre(self, nombre):
        """Mapeo de nombres de nodos a puertos"""
        puertos = {
            'nodo1': 8081,
            'nodo2': 8082,
            'nodo3': 8083,
            'nodo4': 8084,
            'nodo5': 8085
        }
        return puertos.get(nombre, 8081)