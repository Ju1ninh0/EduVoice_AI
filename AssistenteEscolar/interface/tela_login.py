import customtkinter as ctk
from AssistenteEscolar.interface.app_gui import AppGUI

class TelaLogin(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Login — EduVoice")
        self.geometry("400×360")
        self.resizable(False, False)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        frame = ctk.CTkFrame(self, corner_radius=16)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text="🔐 Login", font=ctk.CTkFont(size=22, weight="bold"))
        title.grid(row=0, column=0, pady=(10, 20))

        self.entry_user = ctk.CTkEntry(frame, placeholder_text="Usuário")
        self.entry_pass = ctk.CTkEntry(frame, placeholder_text="Senha", show="•")
        self.entry_user.grid(row=1, column=0, padx=40, pady=10, sticky="ew")
        self.entry_pass.grid(row=2, column=0, padx=40, pady=10, sticky="ew")

        self.label_status = ctk.CTkLabel(frame, text="", text_color="red")
        self.label_status.grid(row=3, column=0, pady=5)

        btn_login = ctk.CTkButton(frame, text="Entrar", command=self.verificar_login)
        btn_login.grid(row=4, column=0, pady=20)

        def alternar_tema(event=None):
            tema = ctk.get_appearance_mode()
            if tema == "Light":
                ctk.set_appearance_mode("dark")
                btn_tema.configure(text="☀️")
            else:
                ctk.set_appearance_mode("light")
                btn_tema.configure(text="🌙")

        btn_tema = ctk.CTkLabel(
            self,
            text="🌙",
            font=ctk.CTkFont(size=18),
            cursor="hand2"
        )
        btn_tema.place(relx=0.95, rely=0.07, anchor="ne")
        btn_tema.bind("<Button-1>", alternar_tema)

    def verificar_login(self):
        usuario = self.entry_user.get().strip()
        senha = self.entry_pass.get().strip()

        if usuario == "admin" and senha == "123":
            tema_atual = ctk.get_appearance_mode()
            self.destroy()
            app = AppGUI(tema=tema_atual)
            app.mainloop()
        else:
            self.label_status.configure(text="Usuário ou senha incorretos.")


if __name__ == "__main__":
    app = TelaLogin()
    app.mainloop()