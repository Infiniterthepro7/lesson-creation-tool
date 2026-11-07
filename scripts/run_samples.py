from dotenv import load_dotenv
load_dotenv()
"""Run both required task examples. Requires configured API key for AI content."""
import argparse
from pathlib import Path
from lessontool.config import Settings
from lessontool.pipeline import Pipeline
from lessontool.store import ProjectStore
from lessontool.exporter import export
SAMPLES=[('HTTP Requests and Responses','Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.'),('SQL Joins: INNER, LEFT and RIGHT','Explain how INNER, LEFT, and RIGHT joins combine rows from two tables and predict the result set for a given pair of small tables.')]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--only',type=int,choices=[1,2]); a=ap.parse_args(); s=Settings.from_env(); store=ProjectStore(s.data_dir); pipe=Pipeline(store,s)
    for i,(title,obj) in enumerate(SAMPLES,1):
        if a.only and a.only!=i: continue
        p=store.create(title,obj); pipe.run_all(p['id'],blocking=True); p=store.get(p['id']); out=Path('samples')/str(i)
        out.mkdir(parents=True,exist_ok=True); data,name,_=export(p,'zip'); (out/name).write_bytes(data)
        print(title, {k:v['status'] for k,v in p['steps'].items()}, '->',out/name)
if __name__=='__main__': main()
