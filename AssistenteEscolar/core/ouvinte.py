import speech_recognition as sr

class OuvinteVoz:
    def __init__(self):
        self.r = sr.Recognizer()
        self.mic = sr.Microphone()
    def ouvir(self):
        with self.mic as source:
            self.r.adjust_for_ambient_noise(source, duration=0.6)
            audio = self.r.listen(source, phrase_time_limit=15)
        try:
            return self.r.recognize_google(audio, language="pt-BR")
        except Exception:
            return ""