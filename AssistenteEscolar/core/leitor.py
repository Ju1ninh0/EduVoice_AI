import os
import time
import tempfile
import pygame
from gtts import gTTS


class LeitorVoz:
    """Classe para leitura de texto em voz usando gTTS e pygame."""

    def __init__(self):
        """Inicializa o leitor de voz."""
        self._mixer_init = False
        self._tmpdir = tempfile.gettempdir()
        self._audio_atual = None

    def _ensure_mixer(self):
        """Inicializa o mixer do pygame se necessário."""
        if not self._mixer_init:
            pygame.mixer.init()
            self._mixer_init = True

    def falar(self, texto):
        """
        Converte texto em fala e reproduz.

        Args:
            texto: String com o texto a ser convertido em fala

        Returns:
            Caminho do arquivo MP3 gerado

        Raises:
            ValueError: Se o texto estiver vazio
        """
        if not texto.strip():
            raise ValueError("Texto vazio")

        mp3_path = os.path.join(self._tmpdir, f"voz_{int(time.time() * 1000)}.mp3")
        tts = gTTS(texto, lang="pt")
        tts.save(mp3_path)

        self._ensure_mixer()
        pygame.mixer.music.load(mp3_path)
        pygame.mixer.music.play()

        self._audio_atual = mp3_path
        return mp3_path

    def aguardar_audio(self):
        """Aguarda a conclusão da reprodução de áudio."""
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    def parar(self):
        """Para a reprodução de áudio."""
        if self._mixer_init:
            pygame.mixer.music.stop()

    def limpar(self):
        """Remove arquivos de áudio temporários."""
        if self._audio_atual and os.path.exists(self._audio_atual):
            try:
                os.remove(self._audio_atual)
                self._audio_atual = None
            except OSError:
                pass