import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR))

from AssistenteEscolar.main import run

if __name__ == "__main__":
    print("🚀 Iniciando o Assistente Escolar completo...")
    run()