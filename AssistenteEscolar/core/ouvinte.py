import speech_recognition as sr
import time

class OuvinteVoz:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def ouvir(self):
        try:
            with sr.Microphone() as mic:
                self.recognizer.adjust_for_ambient_noise(mic, duration=0.5)
                print("🎙️ Ouvindo... fale algo!")
                audio = self.recognizer.listen(mic, timeout=5, phrase_time_limit=15)
            texto = self.recognizer.recognize_google(audio, language="pt-BR")
            print(f"✅ Você disse: {texto}")
            return texto
        except sr.WaitTimeoutError:
            print("⏳ Tempo limite atingido, nenhuma fala detectada.")
            return ""
        except sr.UnknownValueError:
            print("🤔 Não foi possível entender o áudio.")
            return ""
        except Exception as e:
            print(f"❌ Erro ao ouvir: {e}")
            return ""