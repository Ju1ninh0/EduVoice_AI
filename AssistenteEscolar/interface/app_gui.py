import os, time, sqlite3, tempfile, threading, datetime
import customtkinter as ctk
from gtts import gTTS
import pygame
import speech_recognition as sr
import nltk
from nltk.tokenize import sent_tokenize
nltk.download("punkt", quiet=True)

class AssistenteBase:
    def __init__(self, nome="EduVoice"):
        self.nome = nome

class LeitorVoz(AssistenteBase):
    def __init__(self, nome="Leitor"):
        super().__init__(nome)
        self._mixer_init = False
        self._tmpdir = tempfile.gettempdir()

    def _ensure_mixer(self):
        if not self._mixer_init:
            pygame.mixer.init()
            self._mixer_init = True

    def falar(self, texto: str):
        if not texto.strip():
            raise ValueError("Texto vazio")
        mp3_path = os.path.join(self._tmpdir, f"voz_{int(time.time())}.mp3")
        tts = gTTS(texto, lang="pt")
        tts.save(mp3_path)
        self._ensure_mixer()
        pygame.mixer.music.load(mp3_path)
        pygame.mixer.music.play()
        return mp3_path

    def aguardaraudio(self):
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    def parar(self):
        if self._mixer_init:
            pygame.mixer.music.stop()

class OuvinteVoz(AssistenteBase):
    def __init__(self, nome="Ouvinte"):
        super().__init__(nome)
        self.r = sr.Recognizer()

    def ouvir(self) -> str:
        try:
            with sr.Microphone() as mic:
                self.r.adjust_for_ambient_noise(mic, duration=0.5)
                audio = self.r.listen(mic, timeout=5, phrase_time_limit=15)
            texto = self.r.recognize_google(audio, language="pt-BR")
            return texto
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception:
            return ""

class AnalisadorTexto(AssistenteBase):
    def __init__(self, nome="Analisador"):
        super().__init__(nome)

    def resumir(self, texto: str) -> str:
        frases = sent_tokenize(texto, language="portuguese")
        if len(frases) <= 2:
            return texto.strip() if texto.strip() else ""
        n = max(1, len(frases)//2)
        return " ".join(frases[:n])

class Persistencia(AssistenteBase):
    def __init__(self, db_path="historico_eduvoice.db"):
        super().__init__("Persistencia")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            acao TEXT NOT NULL,
            entrada TEXT,
            saida TEXT
        )
        """)
        con.commit()
        con.close()

    def salvar(self, acao: str, entrada: str, saida: str):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO historico(ts, acao, entrada, saida) VALUES(?,?,?,?)",
            (datetime.datetime.now().isoformat(timespec="seconds"), acao, entrada, saida),
        )
        con.commit()
        con.close()

    def listar(self, limite=30):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT ts, acao, substr(entrada,1,80), substr(saida,1,120) FROM historico ORDER BY id DESC LIMIT ?",
            (limite,),
        )
        rows = cur.fetchall()
        con.close()
        return rows

class AppGUI(ctk.CTk, AssistenteBase):
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        super().__init__()
        AssistenteBase.__init__(self, "EduVoice GUI")
        self.geometry("980x680")
        self.minsize(920, 640)
        self.title("Assistente de Inclusão Escolar — EduVoice")
        self.leitor = LeitorVoz()
        self.ouvinte = OuvinteVoz()
        self.analisador = AnalisadorTexto()
        self.db = Persistencia()
        self._tocando = False
        self._build_ui()
        self._carregar_historico()

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main = ctk.CTkFrame(self, corner_radius=16)
        main.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)

        header = ctk.CTkFrame(main, height=64, corner_radius=16)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(8,12))
        header.grid_columnconfigure(0, weight=1)
        title = ctk.CTkLabel(header, text="Assistente de Inclusão Escolar — EduVoice",
                              font=ctk.CTkFont(size=22, weight="bold"))
        subtitle = ctk.CTkLabel(header, text="Leitura em voz alta • Resumo de texto • Voz → Texto",
                                font=ctk.CTkFont(size=14))
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(10,0))
        subtitle.grid(row=1, column=0, sticky="w", padx=16, pady=(0,10))

        left = ctk.CTkFrame(main, corner_radius=16)
        left.grid(row=1, column=0, sticky="nsew", padx=(8,6), pady=(0,8))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        lbl_in = ctk.CTkLabel(left, text="Texto de entrada", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_in.grid(row=0, column=0, sticky="w", padx=12, pady=(12,4))

        self.txt_in = ctk.CTkTextbox(left, height=260, corner_radius=12)
        self.txt_in.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0,12))

        actions = ctk.CTkFrame(left, corner_radius=12)
        actions.grid(row=2, column=0, sticky="ew", padx=12, pady=(0,12))
        actions.grid_columnconfigure((0,1,2,3), weight=1)

        self.btn_ler = ctk.CTkButton(actions, text="🔊 Ler Texto", command=self._on_ler)
        self.btn_falar = ctk.CTkButton(actions, text="🎙️ Voz → Texto", command=self._on_ouvir)
        self.btn_resumir = ctk.CTkButton(actions, text="📚 Resumir", command=self._on_resumir)
        self.btn_parar = ctk.CTkButton(actions, text="⏹ Parar Áudio", command=self._on_parar)
        self.btn_ler.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        self.btn_falar.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        self.btn_resumir.grid(row=0, column=2, padx=8, pady=8, sticky="ew")
        self.btn_parar.grid(row=0, column=3, padx=8, pady=8, sticky="ew")

        lbl_out = ctk.CTkLabel(left, text="Saída / Resumo", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_out.grid(row=3, column=0, sticky="w", padx=12, pady=(0,4))
        self.txt_out = ctk.CTkTextbox(left, height=160, corner_radius=12)
        self.txt_out.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0,12))

        bottom = ctk.CTkFrame(left, corner_radius=12)
        bottom.grid(row=5, column=0, sticky="ew", padx=12, pady=(0,12))
        bottom.grid_columnconfigure((0,1,2), weight=1)
        self.btn_salvar = ctk.CTkButton(bottom, text="💾 Salvar no Histórico", command=self._on_salvar)
        self.btn_limpar = ctk.CTkButton(bottom, text="🧹 Limpar", command=self._on_limpar)
        self.btn_copiar = ctk.CTkButton(bottom, text="📋 Copiar Saída", command=self._on_copiar)
        self.btn_salvar.grid(row=0, column=0, padx=6, pady=8, sticky="ew")
        self.btn_limpar.grid(row=0, column=1, padx=6, pady=8, sticky="ew")
        self.btn_copiar.grid(row=0, column=2, padx=6, pady=8, sticky="ew")

        right = ctk.CTkFrame(main, corner_radius=16)
        right.grid(row=1, column=1, sticky="nsew", padx=(6,8), pady=(0,8))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        lbl_hist = ctk.CTkLabel(right, text="Histórico", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_hist.grid(row=0, column=0, sticky="w", padx=12, pady=(12,4))

        self.hist_box = ctk.CTkTextbox(right, state="disabled", corner_radius=12)
        self.hist_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0,12))

        self.status = ctk.CTkLabel(self, text="Pronto", anchor="w")
        self.status.grid(row=1, column=0, sticky="ew", padx=16, pady=(0,10))

    def _set_status(self, msg: str):
        self.status.configure(text=msg)
        self.update_idletasks()

    def _append_hist_view(self, linhas):
        self.hist_box.configure(state="normal")
        self.hist_box.delete("1.0", "end")
        for ts, acao, entrada, saida in linhas:
            self.hist_box.insert("end", f"[{ts}] {acao}\n")
            if entrada: self.hist_box.insert("end", f"  In: {entrada}\n")
            if saida: self.hist_box.insert("end", f"  Out: {saida}\n")
            self.hist_box.insert("end", "—"*40 + "\n")
        self.hist_box.configure(state="disabled")

    def _carregar_historico(self):
        linhas = self.db.listar(30)
        self._append_hist_view(linhas)

    def _on_ler(self):
        texto = self.txt_in.get("1.0", "end").strip()
        if not texto:
            self._set_status("Nenhum texto para ler.")
            return
        self._set_status("Gerando áudio…")
        def run():
            try:
                self.leitor.parar()
                mp3 = self.leitor.falar(texto)
                self._set_status("Reproduzindo…")
                self._tocando = True
                self.leitor.aguardaraudio()
                self._tocando = False
                self.db.salvar("LerTexto", texto, f"[áudio]{os.path.basename(mp3)}")
                self._carregar_historico()
                self._set_status("Leitura concluída.")
            except Exception as e:
                self._set_status(f"Erro ao ler: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _on_parar(self):
        try:
            self.leitor.parar()
            self._tocando = False
            self._set_status("Áudio parado.")
        except Exception:
            self._set_status("Não foi possível parar o áudio.")

    def _on_ouvir(self):
        self._set_status("Ouvindo microfone…")
        def run():
            try:
                texto = self.ouvinte.ouvir()
                if texto:
                    self.txt_out.insert("end", f"(Voz) {texto}\n")
                    self.db.salvar("Voz->Texto", "", texto)
                    self._carregar_historico()
                    self._set_status("Voz convertida com sucesso.")
                else:
                    self._set_status("Nada reconhecido.")
            except Exception as e:
                self._set_status(f"Erro ao ouvir: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _on_resumir(self):
        texto = self.txt_in.get("1.0", "end").strip()
        if not texto:
            self._set_status("Nenhum texto para resumir.")
            return
        self._set_status("Resumindo…")
        def run():
            try:
                resumo = self.analisador.resumir(texto)
                if not resumo.strip():
                    resumo = "Sem conteúdo para resumir."
                self.txt_out.insert("end", f"(Resumo) {resumo}\n")
                self.db.salvar("Resumo", texto[:4000], resumo[:4000])
                self._carregar_historico()
                self._set_status("Resumo concluído.")
            except Exception as e:
                self._set_status(f"Erro ao resumir: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _on_salvar(self):
        entrada = self.txt_in.get("1.0", "end").strip()
        saida = self.txt_out.get("1.0", "end").strip()
        self.db.salvar("Salvar", entrada[:4000], saida[:4000])
        self._carregar_historico()
        self._set_status("Registro salvo no histórico.")

    def _on_limpar(self):
        self.txt_in.delete("1.0", "end")
        self.txt_out.delete("1.0", "end")
        self._set_status("Limpo.")

    def _on_copiar(self):
        saida = self.txt_out.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(saida)
        self._set_status("Saída copiada.")

if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()