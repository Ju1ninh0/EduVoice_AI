import customtkinter as ctk
import time
import threading

class MinimalIphoneSplash(ctk.CTkToplevel):
    def __init__(self, master, on_finish=None):
        super().__init__(master)
        self.master = master
        self.on_finish = on_finish

        ctk.set_appearance_mode("dark")

        self.geometry("600x400+400+200")
        self.overrideredirect(True)
        self.configure(fg_color="#000000")
        self.attributes("-alpha", 0)

        self.canvas = ctk.CTkCanvas(self, width=600, height=400, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.draw_icon_and_name()

        self.bar_bg = ctk.CTkFrame(self, fg_color="#1a1a1a", width=260, height=6, corner_radius=3)
        self.bar_bg.place(relx=0.5, rely=0.78, anchor="center")

        self.bar = ctk.CTkFrame(self, fg_color="#00aaff", width=1, height=6, corner_radius=3)
        self.bar.place(relx=0.5, rely=0.78, anchor="w", x=-130)

        self.after(100, lambda: threading.Thread(target=self.animate, daemon=True).start())

    def draw_icon_and_name(self):
        x, y = 300, 150
        size = 70

        self.canvas.create_rectangle(
            x - size/2, y - size/2,
            x + size/2, y + size/2,
            outline="#00aaff",
            width=3
        )

        self.canvas.create_text(
            300, 230,
            text="EduVoice",
            fill="#e6e6e6",
            font=("Helvetica", 26, "bold")
        )

    def animate(self):
        for i in range(0, 100):
            self.attributes("-alpha", i/100)
            time.sleep(0.01)

        for i in range(1, 261):
            self.bar.configure(width=i)
            time.sleep(0.006)

        time.sleep(0.4)

        for i in range(100, -1, -1):
            self.attributes("-alpha", i/100)
            time.sleep(0.01)

        self.destroy()

        if self.on_finish:
            self.master.after(10, self.on_finish)