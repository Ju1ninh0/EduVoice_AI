import os
import time
import tempfile
import pygame
from gtts import gTTS

class LeitorVoz:
    def __init__(self):
        self._mixer_init = False
        self._tmpdir = tempfile.gettempdir()

    def _ensure_mixer(self):
        if not self._mixer_init:
            pygame.mixer.init()
            self._mixer_init = True

    def falar(self, texto):
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