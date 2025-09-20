import sys
from modelo.nodo import Nodo
from vista.interfaz_nodo import InterfazNodo
from controlador.controlador_nodo import ControladorNodo

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python app.py <nombre_nodo>")
        sys.exit(1)
    
    nombre_nodo = sys.argv[1]
    
    # Asignar puerto basado en el nombre
    puertos = {
        'nodo1': 8081,
        'nodo2': 8082,
        'nodo3': 8083,
        'nodo4': 8084,
        'nodo5': 8085
    }
    
    puerto = puertos.get(nombre_nodo, 8081)
    
    modelo = Nodo(nombre_nodo, puerto)
    vista = InterfazNodo()
    controlador = ControladorNodo(modelo, vista)
    
    controlador.iniciar_sistema()