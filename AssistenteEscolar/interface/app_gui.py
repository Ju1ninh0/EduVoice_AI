import sounddevice as sd
import numpy as np
import speech_recognition as sr
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
    def __init__(self, nome="Ouvinte", samplerate=16000):
        super().__init__(nome)
        self.r = sr.Recognizer()
        self.samplerate = samplerate
        self.channels = 1
        self.sample_width = 2 

    def ouvir(self, duration=8):
        try:
            print(f"[OuvinteVoz] Gravando áudio por {duration}s...")
            
            grava = sd.rec(
                int(duration * self.samplerate),
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="int16"
            )
            sd.wait()

            if grava.ndim > 1:
                grava = grava[:, 0]

            raw_bytes = grava.tobytes()

            audio_data = sr.AudioData(raw_bytes, self.samplerate, self.sample_width)

            texto = self.r.recognize_google(audio_data, language="pt-BR")
            print("[OuvinteVoz] Texto reconhecido:", texto)

            return texto

        except Exception as e:
            print("ERRO OuvinteVoz (sounddevice):", e)
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
        self.title("EduVoice — Assistente Escolar")

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
            text="EduVoice",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        titulo.grid(row=0, column=0, pady=(25, 30), padx=20, sticky="w")

        self._btn_inicio = ctk.CTkButton(
            self.sidebar,
            text="Início",
            command=lambda: self._mostrar("inicio"),
        )
        self._btn_leitura = ctk.CTkButton(
            self.sidebar,
            text="Ler Texto",
            command=lambda: self._mostrar("leitura"),
        )
        self._btn_voz = ctk.CTkButton(
            self.sidebar,
            text="Voz para Texto",
            command=lambda: self._mostrar("voz"),
        )
        self._btn_resumo = ctk.CTkButton(
            self.sidebar,
            text="Resumo",
            command=lambda: self._mostrar("resumo"),
        )
        self._btn_atividade = ctk.CTkButton(
            self.sidebar,
            text="Atividade",
            command=lambda: self._mostrar("atividade"),
        )
        self._btn_rotina = ctk.CTkButton(
            self.sidebar,
            text="Rotina",
            command=lambda: self._mostrar("rotina"),
        )
        self._btn_hist = ctk.CTkButton(
            self.sidebar,
            text="Histórico",
            command=self._popup_historico,
        )
        self._btn_config = ctk.CTkButton(
            self.sidebar,
            text="Configurações",
            command=lambda: self._mostrar("config"),
        )

        self._btn_inicio.grid(row=1, column=0, padx=20, pady=6, sticky="ew")
        self._btn_leitura.grid(row=2, column=0, padx=20, pady=6, sticky="ew")
        self._btn_voz.grid(row=3, column=0, padx=20, pady=6, sticky="ew")
        self._btn_resumo.grid(row=4, column=0, padx=20, pady=6, sticky="ew")
        self.__juninho_dev = "@Ju1ninh0"
        self._btn_atividade.grid(row=5, column=0, padx=20, pady=6, sticky="ew")
        self._btn_rotina.grid(row=6, column=0, padx=20, pady=6, sticky="ew")
        self._btn_hist.grid(row=7, column=0, padx=20, pady=6, sticky="ew")
        self._btn_config.grid(row=8, column=0, padx=20, pady=6, sticky="ew")

        self.toggle = ctk.CTkButton(
            self.sidebar,
            text="Tema",
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
        self._pages["rotina"] = self._build_rotina

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
            text="Leitura em voz alta",
            height=40,
            command=lambda: self._mostrar("leitura"),
        )
        btn2 = ctk.CTkButton(
            cards,
            text="Resumos automáticos",
            height=40,
            command=lambda: self._mostrar("resumo"),
        )
        btn3 = ctk.CTkButton(
            cards,
            text="Voz para texto",
            height=40,
            command=lambda: self._mostrar("voz"),
        )
        btn4 = ctk.CTkButton(
            cards,
            text="Atividades escolares",
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
            text="Ler",
            width=150,
            command=self._on_ler,
        ).grid(row=0, column=0, padx=6)
        ctk.CTkButton(
            btns,
            text="Parar",
            width=150,
            command=self._on_parar,
        ).grid(row=0, column=1, padx=6)

        ctk.CTkButton(
            f,
            text="Salvar no histórico",
            command=self._salvar_leitura_hist,
        ).pack(pady=(0, 10))

        return f

    def _build_voz(self):
        f = ctk.CTkFrame(self.frame_principal)

        lbl = ctk.CTkLabel(
            f,
            text="Voz para Texto",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        lbl.pack(pady=15)

        self.txt_out_voz = ctk.CTkTextbox(f, height=200)
        self.txt_out_voz.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkButton(
            f,
            text="Ouvir e Transcrever",
            width=180,
            command=self._on_ouvir,
        ).pack(pady=10)

        ctk.CTkButton(
            f,
            text="Salvar transcrição",
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

        self.txt_resumo_in = ctk.CTKTextbox(f, height=200)
        self.txt_resumo_in.pack(fill="both", expand=True, padx=20, pady=8)

        self.txt_resumo_out = ctk.CTKTextbox(f, height=150)
        self.txt_resumo_out.pack(fill="both", expand=True, padx=20, pady=8)

        btns = ctk.CTkFrame(f)
        btns.pack(pady=10)

        ctk.CTkButton(
            btns,
            text="Resumir",
            width=150,
            command=self._on_resumir,
        ).grid(row=0, column=0, padx=6)
        ctk.CTkButton(
            btns,
            text="Exportar resumo",
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
            text="Gerar Atividade",
            command=self._gerar_atividade,
        ).grid(row=0, column=0, padx=6)
        ctk.CTkButton(
            btns,
            text="Exportar atividade",
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
            text="Alternar Tema",
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
            text="Modo Foco de Escrita",
            width=230,
            command=self._modo_foco,
        ).pack(pady=6)

        ctk.CTkButton(
            f,
            text="Ver gráfico de uso",
            width=230,
            command=self._popup_grafico_uso,
        ).pack(pady=6)

        return f

    def _build_rotina(self):
        f = ctk.CTkFrame(self.frame_principal)

        title = ctk.CTkLabel(
            f,
            text="Rotina Inteligente",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.pack(pady=(30, 10))

        subtitle = ctk.CTkLabel(
            f,
            text="Monte sua rotina de forma simples e organizada",
            font=ctk.CTkFont(size=16),
        )
        subtitle.pack(pady=(0, 20))

        container = ctk.CTkFrame(f, corner_radius=20)
        container.pack(padx=40, pady=10, fill="x")

        self.entry_acordar = ctk.CTkEntry(container, placeholder_text="Horário que você acorda", height=40)
        self.entry_faculdade = ctk.CTkEntry(container, placeholder_text="Horário da faculdade", height=40)
        self.entry_almoco = ctk.CTkEntry(container, placeholder_text="Tempo de almoço", height=40)
        self.entry_estudo = ctk.CTkEntry(container, placeholder_text="Tempo de estudo", height=40)
        self.entry_objetivo = ctk.CTkEntry(container, placeholder_text="Objetivo do dia", height=40)
        self.entry_tarefas = ctk.CTkEntry(container, placeholder_text="Tarefas obrigatórias", height=40)

        self.entry_acordar.pack(pady=6, padx=20, fill="x")
        self.entry_faculdade.pack(pady=6, padx=20, fill="x")
        self.entry_almoco.pack(pady=6, padx=20, fill="x")
        self.entry_estudo.pack(pady=6, padx=20, fill="x")
        self.entry_objetivo.pack(pady=6, padx=20, fill="x")
        self.entry_tarefas.pack(pady=6, padx=20, fill="x")

        gerar_btn = ctk.CTkButton(
            f,
            text="Gerar Rotina",
            height=45,
            font=ctk.CTkFont(size=17, weight="bold"),
            command=self._gerar_rotina_inteligente
        )
        gerar_btn.pack(pady=20)

        self.box_rotina = ctk.CTkTextbox(f, height=250, font=ctk.CTkFont(size=15))
        self.box_rotina.pack(padx=25, pady=10, fill="both", expand=True)

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

        registros = self.db.listar()

        for ts, acao, ent, sai in registros:
            box.insert("end", f"[{ts}] {acao}\n")
            if ent:
                box.insert("end", f"  Texto: {ent[:300]}...\n")

            if "foco_" in sai:
                def abrir_arquivo(nome=sai.replace("Arquivo salvo: ", "").strip()):
                    try:
                        with open(nome, "r", encoding="utf-8") as f:
                            conteudo = f.read()

                        modal = ctk.CTkToplevel(self)
                        modal.title(nome)
                        modal.geometry("800x600")

                        txt = ctk.CTkTextbox(modal)
                        txt.pack(fill="both", expand=True, padx=20, pady=20)
                        txt.insert("1.0", conteudo)

                    except Exception as e:
                        self._set_status(f"Erro ao abrir arquivo: {e}")

                btn = ctk.CTkButton(
                    win,
                    text=f"Abrir {sai.replace('Arquivo salvo: ', '')}",
                    width=180,
                    command=abrir_arquivo,
                )
                box.window_create("end", window=btn)
                box.insert("end", "\n")

            elif sai:
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
                text="matplotlib não está instalado. Instale com: pip install matplotlib",
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

        def reabrir_ultimo():
            registros = self.db.listar(limite=1)
            if registros:
                acao = registros[0][1]
                saida = registros[0][3]

                if acao == "ModoFoco" and "foco_" in saida:
                    nome = saida.replace("Arquivo salvo: ", "").strip()
                    try:
                        with open(nome, "r", encoding="utf-8") as f:
                            conteudo = f.read()
                            txt.delete("1.0", "end")
                            txt.insert("1.0", conteudo)
                            self._set_status(f"Último foco carregado: {nome}")
                    except:
                        self._set_status("Não foi possível abrir o último foco.")
                else:
                    self._set_status("Nenhum foco salvo encontrado.")
            else:
                self._set_status("Nenhum foco salvo encontrado.")

        ctk.CTkButton(
            win,
            text="Reabrir último foco",
            width=180,
            command=reabrir_ultimo,
        ).pack(pady=5)

        def salvar():
            conteudo = txt.get("1.0", "end").strip()
            if not conteudo:
                return
            nome = f"foco_{int(time.time())}.txt"
            with open(nome, "w", encoding="utf-8") as arq:
                arq.write(conteudo)
            self.db.salvar("ModoFoco", conteudo, f"Arquivo salvo: {nome}")
            self._set_status(f"Modo foco salvo em {nome}")

        ctk.CTkButton(
            win,
            text="Salvar texto do foco",
            width=180,
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
                try:
                    self.db.salvar("Voz->Texto", "", txt)
                except Exception as e:
                    print("ERRO salvar DB:", e)
                def gui_update():
                    if hasattr(self, "txt_out_voz"):
                        try:
                            self.txt_out_voz.insert("end", txt + "\n")
                        except Exception as e:
                            print("ERRO inserindo no textbox:", e)
                    self._set_status("Voz convertida com sucesso.")
                self.after(0, gui_update)
            else:
                self.after(0, lambda: self._set_status("Nada reconhecido."))
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

    def _gerar_rotina_inteligente(self):
        acordar = self.entry_acordar.get().strip()
        faculdade = self.entry_faculdade.get().strip()
        almoco = self.entry_almoco.get().strip()
        estudo = self.entry_estudo.get().strip()
        objetivo = self.entry_objetivo.get().strip()
        tarefas = self.entry_tarefas.get().strip()

        rotina = f"""
Rotina Inteligente — EduVoice

Acordar: {acordar}
Faculdade: {faculdade}
Almoço: {almoco}
Estudo do dia: {estudo}

Objetivo do dia:
{objetivo}

Tarefas importantes:
{tarefas}

Sugestão organizada:

{acordar} — Acordar e organizar o ambiente
{faculdade} — Período de aulas ou deslocamento
Após faculdade — Almoço ({almoco})
Tarde — Estudo focado ({estudo}) alinhado ao objetivo
Noite — Resolver tarefas: {tarefas}
Antes de dormir — Revisar objetivo do dia: {objetivo}
"""

        self.box_rotina.delete("1.0", "end")
        self.box_rotina.insert("1.0", rotina)

        self.db.salvar("Rotina", objetivo, rotina)
        self._set_status("Rotina gerada e salva.")


if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()

def _signature():
    return