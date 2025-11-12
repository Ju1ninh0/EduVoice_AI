import os, sys
import customtkinter as ctk

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from AssistenteEscolar.interface.app_gui import AppGUI
except ImportError:
    AppGUI = None

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class TelaLogin(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Login — Assistente Escolar")
        self.geometry("480x380")
        self.resizable(False, False)

        frame = ctk.CTkFrame(self, corner_radius=15)
        frame.pack(expand=True, fill="both", padx=40, pady=40)

        titulo = ctk.CTkLabel(frame, text="Acesso ao Assistente Escolar 🧠",
                              font=ctk.CTkFont(size=20, weight="bold"))
        titulo.pack(pady=(25, 10))

        self.usuario_entry = ctk.CTkEntry(frame, placeholder_text="Usuário", width=250, height=40)
        self.usuario_entry.pack(pady=10)

        self.senha_entry = ctk.CTkEntry(frame, placeholder_text="Senha", width=250, height=40, show="•")
        self.senha_entry.pack(pady=10)

        self.msg = ctk.CTkLabel(frame, text="", text_color="red", font=ctk.CTkFont(size=13))
        self.msg.pack(pady=5)

        btn_login = ctk.CTkButton(frame, text="Entrar", width=200, height=40, command=self.validar_login)
        btn_login.pack(pady=(15, 10))

        btn_sair = ctk.CTkButton(frame, text="Sair", width=200, height=40, fg_color="red", hover_color="#a30000",
                                 command=self.destroy)
        btn_sair.pack(pady=(5, 25))

        ctk.CTkLabel(frame, text="© 2025 — EduVoice", font=ctk.CTkFont(size=12)).pack(side="bottom", pady=10)

    def validar_login(self):
        usuario = self.usuario_entry.get().strip()
        senha = self.senha_entry.get().strip()

        if usuario == "admin" and senha == "1234":
            self.msg.configure(text="Login bem-sucedido! ✅", text_color="green")
            if AppGUI:
                self.destroy()
                AppGUI().mainloop()
        else:
            self.msg.configure(text="Usuário ou senha incorretos.")

if __name__ == "__main__":
    TelaLogin().mainloop()