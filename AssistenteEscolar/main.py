import os
import sys
import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

print("Iniciando Assistente Escolar...")

from interface.app_gui import AppGUI
from core.leitor import LeitorVoz
from core.ouvinte import OuvinteVoz
from core.analisador import AnalisadorTexto
from core.persistencia import Persistencia

if __name__ == "__main__":
    pygame.init()
    
    leitor = LeitorVoz()
    ouvinte = OuvinteVoz()
    analisador = AnalisadorTexto()
    persistencia = Persistencia()
    
    app = AppGUI()
    app.mainloop()
