import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

print("Iniciando Assistente Escolar...")

from AssistenteEscolar.interface.app_gui import AppGUI

if __name__ == "__main__":
    time.sleep(1)
    print("Abrindo interface...")
    app = AppGUI()
    app.mainloop()