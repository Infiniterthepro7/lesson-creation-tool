import json, sqlite3, uuid
from pathlib import Path
from datetime import datetime, timezone

class ProjectStore:
    def __init__(self, data_dir):
        Path(data_dir).mkdir(parents=True,exist_ok=True)
        self.db=str(Path(data_dir)/"projects.sqlite3")
        with self.conn() as c:
            c.execute('''CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,title TEXT,objective TEXT,data TEXT,updated TEXT)''')

    def conn(self):
        c=sqlite3.connect(self.db,timeout=20); c.row_factory=sqlite3.Row; return c

    def create(self,title,objective):
        now=datetime.now(timezone.utc).isoformat(); pid=str(uuid.uuid4())
        p={"id":pid,"title":title,"objective":objective,"lesson":None,"sources":[],"qc":{},"steps":{k:{"status":"pending","error":None,"attempts":0} for k in ["research","generate","qc1","qc2"]},"created":now,"updated":now,"edit_history":[]}
        self.save(p); return p

    def save(self,p):
        p["updated"]=datetime.now(timezone.utc).isoformat()
        with self.conn() as c: c.execute("INSERT OR REPLACE INTO projects VALUES(?,?,?,?,?)",(p["id"],p["title"],p["objective"],json.dumps(p),p["updated"]))
        return p

    def get(self,pid):
        with self.conn() as c: row=c.execute("SELECT data FROM projects WHERE id=?",(pid,)).fetchone()
        return json.loads(row["data"]) if row else None

    def list(self):
        with self.conn() as c: rows=c.execute("SELECT data FROM projects ORDER BY updated DESC").fetchall()
        return [json.loads(x["data"]) for x in rows]
