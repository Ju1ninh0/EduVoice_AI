import os, time, tempfile, pygame
from gtts import gTTS

class LeitorVoz:
    def __init__(self):
        self._mixer = False
        self._tmpdir = tempfile.gettempdir()
        self._mp3 = None
    def _ensure(self):
        if not self._mixer:
            pygame.mixer.init()
            self._mixer = True
    def falar(self, texto):
        if not texto or not texto.strip():
            return None
        path = os.path.join(self._tmpdir, f"voz_{int(time.time()*1000)}.mp3")
        gTTS(text=texto, lang="pt").save(path)
        self._ensure()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        self._mp3 = path
        return path
    def parar(self):
        if self._mixer:
            pygame.mixer.music.stop()