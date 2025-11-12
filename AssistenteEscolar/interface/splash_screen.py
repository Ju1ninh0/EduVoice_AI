import customtkinter as ctk
import threading, time

class SplashScreen(ctk.CTk):
    def __init__(self, abrir_callback):
        super().__init__()
        self.title("Assistente Escolar")
        self.geometry("500x300")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        self.abrir_callback = abrir_callback
        self._montar_ui()
        threading.Thread(target=self._carregar, daemon=True).start()

    def _montar_ui(self):
        self.frame = ctk.CTkFrame(self, corner_radius=16)
        self.frame.pack(expand=True, fill="both", padx=20, pady=20)
        self.lbl = ctk.CTkLabel(self.frame, text="Assistente Escolar", font=ctk.CTkFont(size=28, weight="bold"))
        self.lbl.pack(pady=(60,10))
        self.bar = ctk.CTkProgressBar(self.frame, width=300)
        self.bar.pack(pady=(30,10))
        self.lbl_status = ctk.CTkLabel(self.frame, text="Carregando...", font=ctk.CTkFont(size=14))
        self.lbl_status.pack(pady=10)

    def _carregar(self):
        for i in range(101):
            time.sleep(0.02)
            self.bar.set(i/100)
            self.lbl_status.configure(text=f"Carregando... {i}%")
        self.destroy()
        self.abrir_callback()
