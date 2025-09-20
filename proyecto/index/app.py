from modelo.indexador import Indexador
from vista.interfaz_index import InterfazIndex
from controlador.controlador_index import ControladorIndex

if __name__ == "__main__":
    modelo = Indexador()
    vista = InterfazIndex()
    controlador = ControladorIndex(modelo, vista)
    
    controlador.iniciar_sistema()