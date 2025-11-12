import nltk
from nltk.tokenize import sent_tokenize
nltk.download("punkt", quiet=True)

class AnalisadorTexto:
    def __init__(self):
        pass

    def processar_texto(self, texto):
        frases = sent_tokenize(texto, language="portuguese")
        if len(frases) <= 2:
            return texto.strip()
        n = max(1, len(frases)//2)
        return " ".join(frases[:n])