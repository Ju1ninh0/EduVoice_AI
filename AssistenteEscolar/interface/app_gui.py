import os, time, sqlite3, tempfile, threading, datetime
import customtkinter as ctk
from gtts import gTTS
import pygame
import speech_recognition as sr
import nltk
from nltk.tokenize import sent_tokenize
nltk.download("punkt", quiet=True)

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOT = True
except Exception:
    MATPLOT = False

class AssistenteBase:
    def __init__(self, nome="EduVoice"):
        self.nome = nome

class LeitorVoz(AssistenteBase):
    def __init__(self, nome="Leitor"):
        super().__init__(nome)
        self._mixer_init = False
        self._tmpdir = tempfile.gettempdir()

    def _ensure(self):
        if not self._mixer_init:
            pygame.mixer.init()
            self._mixer_init = True

    def falar(self, texto):
        if not texto.strip():
            raise ValueError("Texto vazio")
        mp3 = os.path.join(self._tmpdir, f"voz_{int(time.time())}.mp3")
        gTTS(texto, lang="pt").save(mp3)
        self._ensure()
        pygame.mixer.music.load(mp3)
        pygame.mixer.music.play()
        return mp3

    def esperar(self):
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    def parar(self):
        if self._mixer_init:
            pygame.mixer.music.stop()

class OuvinteVoz(AssistenteBase):
    def __init__(self, nome="Ouvinte"):
        super().__init__(nome)
        self.r = sr.Recognizer()

    def ouvir(self):
        try:
            with sr.Microphone() as mic:
                self.r.adjust_for_ambient_noise(mic, duration=0.5)
                audio = self.r.listen(mic, timeout=5, phrase_time_limit=15)
            return self.r.recognize_google(audio, language="pt-BR")
        except Exception:
            return ""

class AnalisadorTexto(AssistenteBase):
    def __init__(self, nome="Analisador"):
        super().__init__(nome)

    def resumir(self, texto):
        frases = sent_tokenize(texto, language="portuguese")
        if len(frases) <= 2:
            return texto.strip()
        return " ".join(frases[:max(1, len(frases) // 2)])

class Persistencia(AssistenteBase):
    def __init__(self, db="historico_eduvoice.db"):
        super().__init__("Persistencia")
        self.db = db
        self._init()


    def _init(self):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                acao TEXT NOT NULL,
                entrada TEXT,
                saida TEXT
            )
            """
        )
        con.commit()
        con.close()

    def salvar(self, acao, entrada, saida):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO historico(ts,acao,entrada,saida) VALUES(?,?,?,?)",
            (datetime.datetime.now().isoformat(timespec="seconds"), acao, entrada, saida),
        )
        con.commit()
        con.close()

    def listar(self, limite=40):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        cur.execute(
            """
            SELECT ts,acao,
                   substr(entrada,1,120),
                   substr(saida,1,160)
            FROM historico
            ORDER BY id DESC
            LIMIT ?
            """,
            (limite,),
        )
        r = cur.fetchall()
        con.close()
        return r

    def stats_acoes(self):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        cur.execute(
            """
            SELECT acao, COUNT(*) 
            FROM historico
            GROUP BY acao
            ORDER BY COUNT(*) DESC
            """
        )
        r = cur.fetchall()
        con.close()
        return r

class AppGUI(ctk.CTk, AssistenteBase):
    def __init__(self, tema="dark"):
        ctk.set_appearance_mode(tema)
        ctk.set_default_color_theme("blue")
        ctk.CTk.__init__(self)
        AssistenteBase.__init__(self, "EduVoice")

        self.geometry("1200x750")
        self.minsize(1100, 700)
        self.title("📘 EduVoice — Assistente Escolar")

        self.leitor = LeitorVoz()
        self.ouvinte = OuvinteVoz()
        self.analisador = AnalisadorTexto()
        self.db = Persistencia()

        self._pages = {}

        self._layout()
        self._criar_paginas()
        self._mostrar("inicio")

    def _layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=190, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_rowconfigure(10, weight=1)

        titulo = ctk.CTkLabel(
            self.sidebar,
            text="📘 EduVoice",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        titulo.grid(row=0, column=0, pady=(25, 30), padx=20, sticky="w")

        self._btn_inicio = ctk.CTkButton(
            self.sidebar,
            text="🏠 Início",
            command=lambda: self._mostrar("inicio"),
        )
        self._btn_leitura = ctk.CTkButton(
            self.sidebar,
            text="📖 Ler Texto",
            command=lambda: self._mostrar("leitura"),
        )
        self._btn_voz = ctk.CTkButton(
            self.sidebar,
            text="🎤 Voz → Texto",
            command=lambda: self._mostrar("voz"),
        )
        self._btn_resumo = ctk.CTkButton(
            self.sidebar,
            text="📝 Resumo",
            command=lambda: self._mostrar("resumo"),
        )
        self._btn_atividade = ctk.CTkButton(
            self.sidebar,
            text="📚 Atividade",
            command=lambda: self._mostrar("atividade"),
        )
        self._btn_hist = ctk.CTkButton(
            self.sidebar,
            text="🗂 Histórico",
            command=self._popup_historico,
        )
        self._btn_config = ctk.CTkButton(
            self.sidebar,
            text="⚙ Configurações",
            command=lambda: self._mostrar("config"),
        )

        self._btn_inicio.grid(row=1, column=0, padx=20, pady=6, sticky="ew")
        self._btn_leitura.grid(row=2, column=0, padx=20, pady=6, sticky="ew")
        self._btn_voz.grid(row=3, column=0, padx=20, pady=6, sticky="ew")
        self._btn_resumo.grid(row=4, column=0, padx=20, pady=6, sticky="ew")
        self.__juninho_dev = "@Ju1ninh0"
        self._btn_atividade.grid(row=5, column=0, padx=20, pady=6, sticky="ew")
        self._btn_hist.grid(row=6, column=0, padx=20, pady=6, sticky="ew")
        self._btn_config.grid(row=7, column=0, padx=20, pady=6, sticky="ew")

        self.toggle = ctk.CTkButton(
            self.sidebar,
            text="🌙",
            width=50,
            command=self._alternar_tema,
        )
        self.toggle.grid(row=11, column=0, pady=10)

        self.frame_principal = ctk.CTkFrame(self, corner_radius=0)
        self.frame_principal.grid(row=0, column=1, sticky="nsew")

        self.status_bar = ctk.CTkLabel(self, text="Pronto", anchor="w")
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5))

    def _set_status(self, msg):
        self.status_bar.configure(text=msg)
        self.update_idletasks()

    def _criar_paginas(self):
        self._pages["inicio"] = self._build_inicio
        self._pages["leitura"] = self._build_leitura
        self._pages["voz"] = self._build_voz
        self._pages["resumo"] = self._build_resumo
        self._pages["atividade"] = self._build_atividade
        self._pages["config"] = self._build_config

    def _mostrar(self, nome):
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
        frame = self._pages[nome]()
        frame.pack(fill="both", expand=True)

    def _build_inicio(self):
        f = ctk.CTkFrame(self.frame_principal)

        icon = ctk.CTkLabel(
            f,
            text="📘",
            font=ctk.CTkFont(size=70, weight="bold"),
        )
        icon.pack(pady=(40, 10))

        title = ctk.CTkLabel(
            f,
            text="Bem-vindo ao EduVoice",
            font=ctk.CTkFont(size=32, weight="bold"),
        )
        title.pack(pady=(0, 5))

        subtitle = ctk.CTkLabel(
            f,
            text="Assistente escolar para leitura, escrita e acessibilidade",
            font=ctk.CTkFont(size=18),
        )
        subtitle.pack(pady=(0, 25))

        cards = ctk.CTkFrame(f, corner_radius=18)
        cards.pack(pady=10, padx=80, fill="x")

        btn1 = ctk.CTkButton(
            cards,
            text="📖  Leitura em voz alta",
            height=40,
            command=lambda: self._mostrar("leitura"),
        )
        btn2 = ctk.CTkButton(
            cards,
            text="📝  Resumos automáticos",
            height=40,
            command=lambda: self._mostrar("resumo"),
        )
        btn3 = ctk.CTkButton(
            cards,
            text="🎤  Voz para texto",
            height=40,
            command=lambda: self._mostrar("voz"),
        )
        btn4 = ctk.CTkButton(
            cards,
            text="📚  Atividades escolares",
            height=40,
            command=lambda: self._mostrar("atividade"),
        )

        btn1.pack(pady=8, padx=30, fill="x")
        btn2.pack(pady=8, padx=30, fill="x")
        btn3.pack(pady=8, padx=30, fill="x")
        btn4.pack(pady=8, padx=30, fill="x")

        stats_frame = ctk.CTkFrame(f, corner_radius=18)
        stats_frame.pack(pady=25, padx=80, fill="x")

        lbl_stats = ctk.CTkLabel(
            stats_frame,
            text="Resumo de uso recente",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        lbl_stats.pack(pady=(10, 5))

        stats = self.db.stats_acoes()
        if stats:
            for acao, qtd in stats[:4]:
                txt = f"{acao}: {qtd} registro(s)"
                ctk.CTkLabel(
                    stats_frame,
                    text=txt,
                    font=ctk.CTkFont(size=14),
                ).pack(pady=2)
        else:
            ctk.CTkLabel(
                stats_frame,
                text="Nenhum dado registrado ainda.",
                font=ctk.CTkFont(size=14),
            ).pack(pady=10)

        return f


    def _build_leitura(self):
        f = ctk.CTkFrame(self.frame_principal)

        lbl = ctk.CTkLabel(
            f,
            text="Leitura de Texto",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        lbl.pack(pady=15)

        self.txt_in = ctk.CTkTextbox(f)
        self.txt_in.pack(fill="both", expand=True, padx=20, pady=10)

        btns = ctk.CTkFrame(f)
        btns.pack(pady=10)

        ctk.CTkButton(
            btns,
            text="🔊 Ler",
            width=150,
            command=self._on_ler,
        ).grid(row=0, column=0, padx=6)
        ctk.CTkButton(
            btns,
            text="⏹ Parar",
            width=150,
            command=self._on_parar,
        ).grid(row=0, column=1, padx=6)

        ctk.CTkButton(
            f,
            text="💾 Salvar no histórico",
            command=self._salvar_leitura_hist,
        ).pack(pady=(0, 10))

        return f

    def _build_voz(self):
        f = ctk.CTkFrame(self.frame_principal)

        lbl = ctk.CTkLabel(
            f,
            text="Voz → Texto",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        lbl.pack(pady=15)

        self.txt_out_voz = ctk.CTkTextbox(f, height=200)
        self.txt_out_voz.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkButton(
            f,
            text="🎤 Ouvir e Transcrever",
            width=180,
            command=self._on_ouvir,
        ).pack(pady=10)

        ctk.CTkButton(
            f,
            text="💾 Salvar transcrição",
            command=self._salvar_voz_hist,
        ).pack(pady=5)

        return f

    def _build_resumo(self):
        f = ctk.CTkFrame(self.frame_principal)

        lbl = ctk.CTkLabel(
            f,
            text="Resumo Inteligente",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        lbl.pack(pady=15)

        self.txt_resumo_in = ctk.CTkTextbox(f, height=200)
        self.txt_resumo_in.pack(fill="both", expand=True, padx=20, pady=8)

        self.txt_resumo_out = ctk.CTkTextbox(f, height=150)
        self.txt_resumo_out.pack(fill="both", expand=True, padx=20, pady=8)

        btns = ctk.CTkFrame(f)
        btns.pack(pady=10)

        ctk.CTkButton(
            btns,
            text="📘 Resumir",
            width=150,
            command=self._on_resumir,
        ).grid(row=0, column=0, padx=6)
        ctk.CTkButton(
            btns,
            text="💾 Exportar resumo",
            width=170,
            command=self._exportar_resumo,
        ).grid(row=0, column=1, padx=6)

        return f

    def _build_atividade(self):
        f = ctk.CTkFrame(self.frame_principal)

        lbl = ctk.CTkLabel(
            f,
            text="Gerador de Atividade Escolar",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        lbl.pack(pady=20)

        self.txt_ativ_in = ctk.CTkTextbox(f, height=150)
        self.txt_ativ_in.pack(fill="both", padx=20, pady=10)

        self.txt_ativ_out = ctk.CTkTextbox(f, height=200)
        self.txt_ativ_out.pack(fill="both", expand=True, padx=20, pady=10)

        btns = ctk.CTkFrame(f)
        btns.pack(pady=10)

        ctk.CTkButton(
            btns,
            text="📚 Gerar Atividade",
            command=self._gerar_atividade,
        ).grid(row=0, column=0, padx=6)
        ctk.CTkButton(
            btns,
            text="💾 Exportar atividade",
            command=self._exportar_atividade,
        ).grid(row=0, column=1, padx=6)

        return f

    def _build_config(self):
        f = ctk.CTkFrame(self.frame_principal)

        lbl = ctk.CTkLabel(
            f,
            text="Configurações e Ferramentas Avançadas",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        lbl.pack(pady=20)

        ctk.CTkLabel(
            f,
            text="Tema da interface",
            font=ctk.CTkFont(size=16),
        ).pack(pady=5)
        ctk.CTkButton(
            f,
            text="🌙 Alternar Tema",
            width=200,
            command=self._alternar_tema,
        ).pack(pady=10)

        ctk.CTkLabel(
            f,
            text="Ferramentas avançadas",
            font=ctk.CTkFont(size=16),
        ).pack(pady=(25, 5))

        ctk.CTkButton(
            f,
            text="🧠 Modo Foco de Escrita",
            width=230,
            command=self._modo_foco,
        ).pack(pady=6)

        ctk.CTkButton(
            f,
            text="📊 Ver gráfico de uso",
            width=230,
            command=self._popup_grafico_uso,
        ).pack(pady=6)

        return f

    def _alternar_tema(self):
        tema = ctk.get_appearance_mode()
        if tema == "Light":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def _popup_historico(self):
        win = ctk.CTkToplevel(self)
        win.title("Histórico de uso")
        win.geometry("700x520")

        box = ctk.CTkTextbox(win)
        box.pack(fill="both", expand=True, padx=20, pady=20)

        for ts, acao, ent, sai in self.db.listar():
            box.insert("end", f"[{ts}] {acao}\n")
            if ent:
                box.insert("end", f"  In: {ent}\n")
            if sai:
                box.insert("end", f"  Out: {sai}\n")
            box.insert("end", "-" * 40 + "\n")

        box.configure(state="disabled")

    def _popup_grafico_uso(self):
        stats = self.db.stats_acoes()
        win = ctk.CTkToplevel(self)
        win.title("Gráfico de uso do EduVoice")
        win.geometry("700x500")
        if not stats:
            ctk.CTkLabel(
                win,
                text="Nenhum dado disponível para gerar gráfico.",
                font=ctk.CTkFont(size=16),
            ).pack(pady=40)
            return
        if not MATPLOT:
            ctk.CTkLabel(
                win,
                text="matplotlib não está instalado.\nInstale com: pip install matplotlib",
                font=ctk.CTkFont(size=16),
            ).pack(pady=40)
            return
        acoes = [a for a, _ in stats]
        valores = [v for _, v in stats]
        fig = plt.Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        ax.bar(acoes, valores)
        ax.set_title("Ações registradas")
        ax.set_ylabel("Quantidade")
        ax.set_xlabel("Tipo de ação")
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _modo_foco(self):
        win = ctk.CTkToplevel(self)
        win.title("Modo Foco de Escrita")
        win.geometry("900x600")
        win.grab_set()
        lbl = ctk.CTkLabel(
            win,
            text="Modo Foco — escreva sem distrações",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        lbl.pack(pady=10)
        txt = ctk.CTkTextbox(win, font=ctk.CTkFont(size=16))
        txt.pack(fill="both", expand=True, padx=20, pady=10)
        def salvar():
            conteudo = txt.get("1.0", "end").strip()
            if not conteudo:
                return
            nome = f"foco_{int(time.time())}.txt"
            with open(nome, "w", encoding="utf-8") as arq:
                arq.write(conteudo)
            self.db.salvar("ModoFoco", "", f"Arquivo: {nome}")
            self._set_status(f"Modo foco salvo em {nome}")
        ctk.CTkButton(
            win,
            text="💾 Salvar texto do foco",
            command=salvar,
        ).pack(pady=10)

    def _on_ler(self):
        if not hasattr(self, "txt_in"):
            return
        t = self.txt_in.get("1.0", "end").strip()
        if not t:
            return
        self._set_status("Gerando áudio e lendo texto.")
        def run():
            try:
                mp3 = self.leitor.falar(t)
                self.leitor.esperar()
                self.db.salvar("Leitura", t, f"[audio]{os.path.basename(mp3)}")
                self._set_status("Leitura concluída.")
            except Exception:
                self._set_status("Erro ao ler texto.")
        threading.Thread(target=run, daemon=True).start()

    def _salvar_leitura_hist(self):
        if not hasattr(self, "txt_in"):
            return
        t = self.txt_in.get("1.0", "end").strip()
        if not t:
            return
        self.db.salvar("LeituraManual", t, "")
        self._set_status("Leitura salva no histórico.")

    def _on_parar(self):
        try:
            self.leitor.parar()
            self._set_status("Áudio parado.")
        except Exception:
            self._set_status("Não foi possível parar o áudio.")

    def _on_ouvir(self):
        self._set_status("Ouvindo microfone...")
        def run():
            txt = self.ouvinte.ouvir()
            if txt:
                if hasattr(self, "txt_out_voz"):
                    self.txt_out_voz.insert("end", txt + "\n")
                self.db.salvar("Voz->Texto", "", txt)
                self._set_status("Voz convertida com sucesso.")
            else:
                self._set_status("Nada reconhecido.")
        threading.Thread(target=run, daemon=True).start()

    def _salvar_voz_hist(self):
        if not hasattr(self, "txt_out_voz"):
            return
        conteudo = self.txt_out_voz.get("1.0", "end").strip()
        if not conteudo:
            return
        self.db.salvar("SalvarVozTexto", "", conteudo)
        self._set_status("Transcrição salva no histórico.")

    def _on_resumir(self):
        if not hasattr(self, "txt_resumo_in"):
            return
        t = self.txt_resumo_in.get("1.0", "end").strip()
        if not t:
            return
        self._set_status("Gerando resumo...")
        resumo = self.analisador.resumir(t)
        if hasattr(self, "txt_resumo_out"):
            self.txt_resumo_out.insert("end", resumo + "\n")
        self.db.salvar("Resumo", t, resumo)
        self._set_status("Resumo concluído.")

    def _exportar_resumo(self):
        if not hasattr(self, "txt_resumo_out"):
            return
        conteudo = self.txt_resumo_out.get("1.0", "end").strip()
        if not conteudo:
            return
        nome = f"resumo_{int(time.time())}.txt"
        with open(nome, "w", encoding="utf-8") as arq:
            arq.write(conteudo)
        self.db.salvar("ExportarResumo", "", nome)
        self._set_status(f"Resumo exportado para {nome}")

    def _gerar_atividade(self):
        if not hasattr(self, "txt_ativ_in"):
            return
        texto = self.txt_ativ_in.get("1.0", "end").strip()
        if not texto:
            return
        perguntas = [
            "1) Qual é a ideia principal do texto?",
            "2) Explique com suas palavras um ponto importante mencionado.",
            "3) Crie um título alternativo para o texto.",
            "4) Cite duas informações relevantes presentes no texto.",
            "5) O que você aprendeu com este conteúdo?",
        ]
        out = "\n".join(perguntas)
        if hasattr(self, "txt_ativ_out"):
            self.txt_ativ_out.insert("end", out + "\n")
        self.db.salvar("Atividade", texto, out)
        self._set_status("Atividade gerada.")

    def _exportar_atividade(self):
        if not hasattr(self, "txt_ativ_out"):
            return
        conteudo = self.txt_ativ_out.get("1.0", "end").strip()
        if not conteudo:
            return
        nome = f"atividade_{int(time.time())}.txt"
        with open(nome, "w", encoding="utf-8") as arq:
            arq.write(conteudo)
        self.db.salvar("ExportarAtividade", "", nome)
        self._set_status(f"Atividade exportada para {nome}")

if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()