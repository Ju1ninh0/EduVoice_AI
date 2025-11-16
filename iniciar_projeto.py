import customtkinter as ctk
from splash import MinimalIphoneSplash
from AssistenteEscolar.interface.app_gui import AppGUI

def abrir_app():
    app = AppGUI()
    app.mainloop()

if __name__ == "__main__":
    root = ctk.CTk()  
    root.withdraw()

    splash = MinimalIphoneSplash(root, on_finish=abrir_app)

    root.mainloop()