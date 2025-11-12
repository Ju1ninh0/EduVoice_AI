import sqlite3, datetime

class Persistencia:
    def __init__(self, db_path="historico_assistente_escolar.db"):
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

    def salvar(self, acao, entrada, saida):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO historico(ts, acao, entrada, saida) VALUES(?,?,?,?)",
            (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), acao, entrada, saida)
        )
        con.commit()
        con.close()

    def listar(self, limite=30):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT ts, acao, substr(entrada,1,80), substr(saida,1,120) FROM historico ORDER BY id DESC LIMIT ?",
            (limite,)
        )
        rows = cur.fetchall()
        con.close()
        return rows
