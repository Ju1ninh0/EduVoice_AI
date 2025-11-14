import nltk
from nltk.tokenize import sent_tokenize
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

class AnalisadorTexto:
    def resumir(self, texto):
        sents = sent_tokenize(texto)
        if not sents:
            return ""
        if len(sents) <= 2:
            return texto
        return " ".join(sents[:2])