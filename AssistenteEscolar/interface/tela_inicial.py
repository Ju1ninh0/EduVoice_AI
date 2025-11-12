import customtkinter as ctk
import threading, time

class TelaInicial(ctk.CTk):
    def __init__(self, abrir_app_callback):
        super().__init__()
        self.title("Assistente Escolar")
        self.geometry("900x600")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.abrir_app_callback = abrir_app_callback
        self.tema = "dark"
        self._build_ui()
        self._animar_titulo()

    def _build_ui(self):
        self.frame = ctk.CTkFrame(self, corner_radius=16)
        self.frame.pack(expand=True, fill="both", padx=30, pady=30)
        self.lbl_titulo = ctk.CTkLabel(self.frame, text="Assistente Escolar", font=ctk.CTkFont(size=38, weight="bold"))
        self.lbl_titulo.pack(pady=(80, 10))
        self.lbl_sub = ctk.CTkLabel(self.frame, text="Leitura de texto • Voz → Texto • Resumo automático", font=ctk.CTkFont(size=16))
        self.lbl_sub.pack(pady=(0, 60))
        self.btn_entrar = ctk.CTkButton(self.frame, text="🚀 Entrar no Assistente", height=45, width=220,
                                        font=ctk.CTkFont(size=16, weight="bold"), command=self._abrir_assistente)
        self.btn_entrar.pack(pady=20)
        self.btn_tema = ctk.CTkButton(self.frame, text="☀️ Modo Claro", height=35, width=160, command=self._alternar_tema)
        self.btn_tema.pack(pady=(10, 50))
        self.lbl_rodape = ctk.CTkLabel(self.frame, text="💡 Todo grande projeto começa com um pequeno passo.",
                                       font=ctk.CTkFont(size=13))
        self.lbl_rodape.pack(side="bottom", pady=20)

    def _animar_titulo(self):
        cores = ["#8AB4F8", "#7BA3E6", "#6B92D4", "#5B81C2"]
        def animar():
            i = 0
            while True:
                try:
                    self.lbl_titulo.configure(text_color=cores[i % len(cores)])
                    i += 1
                    time.sleep(0.6)
                except Exception:
                    break
        threading.Thread(target=animar, daemon=True).start()

    def _alternar_tema(self):
        if self.tema == "light":
            ctk.set_appearance_mode("dark")
            self.btn_tema.configure(text="☀️ Modo Claro")
            self.tema = "dark"
        else:
            ctk.set_appearance_mode("light")
            self.btn_tema.configure(text="🌙 Modo Escuro")
            self.tema = "light"

    def _abrir_assistente(self):
        self.destroy()
        self.abrir_app_callback()
