import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time, threading, customtkinter as ctk, nltk, os
from core.leitor import LeitorVoz
from core.ouvinte import OuvinteVoz
from core.analisador import AnalisadorTexto
from core.persistencia import Persistencia

nltk.download("punkt", quiet=True)

class AppGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Assistente Escolar")
        self.geometry("800x500")
        self.resizable(False, False)

        self.persistencia = Persistencia()
        self.ouvinte = OuvinteVoz()
        self.leitor = LeitorVoz()
        self.analisador = AnalisadorTexto()

        self._criar_interface()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _criar_interface(self):
        self.label_titulo = ctk.CTkLabel(self, text="Assistente Escolar", font=("Arial", 26, "bold"))
        self.label_titulo.pack(pady=20)

        self.text_area = ctk.CTkTextbox(self, width=720, height=250, corner_radius=10)
        self.text_area.pack(pady=10)

        frame_botoes = ctk.CTkFrame(self)
        frame_botoes.pack(pady=15)

        self.btn_ouvir = ctk.CTkButton(frame_botoes, text="Ouvir", width=160, command=self._ouvir)
        self.btn_ouvir.grid(row=0, column=0, padx=10)

        self.btn_falar = ctk.CTkButton(frame_botoes, text="Falar", width=160, command=self._falar)
        self.btn_falar.grid(row=0, column=1, padx=10)

        self.btn_limpar = ctk.CTkButton(frame_botoes, text="Limpar", width=160, command=self._limpar_texto)
        self.btn_limpar.grid(row=0, column=2, padx=10)

    def _ouvir(self):
        texto = self.ouvinte.ouvir_usuario()
        self.text_area.insert("end", f"Você: {texto}\n")
        resposta = self.analisador.processar_texto(texto)
        self.text_area.insert("end", f"Assistente: {resposta}\n")
        self.persistencia.salvar_texto("Usuário", texto=texto, resumo=resposta)

    def _falar(self):
        texto = self.text_area.get("1.0", "end").strip()
        if texto:
            self.leitor.ler_texto(texto)

    def _limpar_texto(self):
        self.text_area.delete("1.0", "end")

    def _on_close(self):
        try:
            db_path = os.path.join(os.getcwd(), "historico_assistente_escolar.db")
            if os.path.exists(db_path):
                os.remove(db_path)
                print("📁 Histórico limpo com sucesso.")
        except Exception as e:
            print(f"Erro ao limpar histórico: {e}")
        finally:
            self.destroy()