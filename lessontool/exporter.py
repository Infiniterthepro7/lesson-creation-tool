import io, json, re, zipfile
from datetime import datetime

def slug(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")[:60] or "lesson"

def lesson_md(p):
    l=p.get("lesson") or {}; out=[f"# {l.get('title',p['title'])}",f"**Learning objective:** {l.get('objective',p['objective'])}",f"**Duration:** {l.get('duration_minutes',45)} minutes",f"**Audience:** {l.get('audience','Not specified')}",""]
    for s in l.get("sections",[]): out += [f"## {s.get('heading','Section')} ({s.get('minutes',0)} min)",s.get("content", ""),""]
    if l.get("instructor_notes"): out += ["## Instructor notes",l["instructor_notes"],""]
    out += ["## References"]
    for x in p.get("sources",[]): out.append(f"- [{x.get('title','Source')}]({x.get('url','')}) — {x.get('kind','Source')}. {x.get('snippet','')[:300]}")
    return "\n".join(out)

def export(p,fmt="zip"):
    reports={k:json.dumps(v,indent=2,ensure_ascii=False) for k,v in p.get("qc",{}).items()}
    refs="\n".join(f"- [{s.get('title','Source')}]({s.get('url','')}) ({s.get('kind','Source')})" for s in p.get("sources",[]))
    if fmt=="md": return lesson_md(p).encode(),slug(p['title'])+".md","text/markdown"
    if fmt=="html":
        from markdown import markdown
        html="<!doctype html><meta charset='utf-8'><title>Lesson</title><article>"+markdown(lesson_md(p),extensions=["tables","fenced_code"]) + "</article>"
        return html.encode(),slug(p['title'])+".html","text/html"
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("lesson.md",lesson_md(p)); z.writestr("references.md",refs)
        for k,v in reports.items(): z.writestr(f"{k}_report.json",v)
        z.writestr("project.json",json.dumps(p,indent=2,ensure_ascii=False))
        z.writestr("README.txt","Lesson creation export. Review all sources and QC findings before teaching.\n")
    return b.getvalue(),slug(p['title'])+"-export.zip","application/zip"
