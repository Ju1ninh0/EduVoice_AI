import customtkinter as ctk
from splash import MinimalIphoneSplash
from AssistenteEscolar.interface.app_gui import AppGUI

def abrir_app(root, splash):
    try:
        splash.destroy()
    except Exception:
        pass

    try:
        root.destroy()
    except Exception:
        pass

    app = AppGUI()
    app.mainloop()

if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()

    splash = MinimalIphoneSplash(root, on_finish=lambda: abrir_app(root, splash))

    root.mainloop()

def _signature():
    return