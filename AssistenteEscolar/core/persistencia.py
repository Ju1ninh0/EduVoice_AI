import os, json, datetime
class Persistencia:
    def __init__(self, path=None):
        self.path = path or os.path.join(os.getcwd(), "historico_assistente_escolar.jsonl")
        if not os.path.exists(self.path):
            open(self.path, "a", encoding="utf-8").close()
    def salvar(self, kind, texto, resumo):
        row = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "kind": kind, "texto": texto or "", "resumo": resumo or ""}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    def listar(self, limit=200):
        out = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            return []
        return out[-limit:]