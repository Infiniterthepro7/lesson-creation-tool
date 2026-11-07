from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort
from dotenv import load_dotenv
import io
from lessontool.config import Settings
from lessontool.store import ProjectStore
from lessontool.pipeline import Pipeline
from lessontool.exporter import export

load_dotenv()
def create_app(settings=None, pipeline=None):
    s=settings or Settings.from_env(); store=ProjectStore(s.data_dir); pipe=pipeline or Pipeline(store,s)
    app=Flask(__name__); app.config['MAX_CONTENT_LENGTH']=2*1024*1024
    @app.get('/')
    def home(): return render_template('index.html', projects=store.list(), model=s.model, provider=s.provider, demo=not pipe.llm.available)
    @app.get('/api/projects')
    def projects(): return jsonify(store.list())
    @app.post('/api/projects')
    def create():
        d=request.get_json(silent=True) or {}; title=(d.get('title') or '').strip(); obj=(d.get('objective') or '').strip()
        if not title or not obj: return jsonify(error='Lesson title and learning objective are required.'),400
        p=store.create(title,obj); pipe.run_all(p['id']); return jsonify(p),202
    @app.get('/api/projects/<pid>')
    def get_project(pid):
        p=store.get(pid)
        if not p: abort(404)
        return jsonify(p)
    @app.post('/api/projects/<pid>/retry')
    def retry(pid):
        p=store.get(pid)
        if not p: abort(404)
        d=request.get_json(silent=True) or {}; step=d.get('step')
        allowed={'research','generate','qc1','qc2'}
        if step not in allowed: return jsonify(error='Choose research, generate, qc1 or qc2.'),400
        if step=='research':
            p['steps']['research'].update(status='pending',error=None); p['steps']['generate'].update(status='pending',error=None); p['steps']['qc1'].update(status='pending',error=None); p['steps']['qc2'].update(status='pending',error=None)
        elif step=='generate':
            p['steps']['generate'].update(status='pending',error=None); p['steps']['qc1'].update(status='pending',error=None); p['steps']['qc2'].update(status='pending',error=None)
        else: p['steps'][step].update(status='pending',error=None)
        store.save(p); pipe.run_all(pid); return jsonify(p),202
    @app.put('/api/projects/<pid>/lesson')
    def edit(pid):
        p=store.get(pid)
        if not p: abort(404)
        d=request.get_json(silent=True) or {}; lesson=d.get('lesson')
        if not isinstance(lesson,dict): return jsonify(error='Lesson object is required.'),400
        p['edit_history'].append({'at':p['updated'],'lesson':p.get('lesson')}); p['lesson']=lesson; store.save(p); return jsonify(p)
    @app.get('/api/projects/<pid>/export')
    def download(pid):
        p=store.get(pid)
        if not p: abort(404)
        data,name,mime=export(p,request.args.get('format','zip'))
        return send_file(io.BytesIO(data),as_attachment=True,download_name=name,mimetype=mime)
    @app.get('/api/config')
    def config(): return jsonify({'provider':s.provider,'model':s.model,'demo_mode':not pipe.llm.available,'lesson_minutes':s.lesson_minutes})
    return app

if __name__=='__main__':
    settings=Settings.from_env(); Path(settings.data_dir).mkdir(exist_ok=True,parents=True)
    create_app(settings).run(host='127.0.0.1',port=settings.port,debug=True)
