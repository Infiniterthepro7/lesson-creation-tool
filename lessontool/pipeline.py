import json, re, threading
from .search import WebSearch, search_books, fetch_page
from .llm import LLMClient

class Pipeline:
    def __init__(self, store, settings): self.store=store; self.s=settings; self.llm=LLMClient(settings); self.search=WebSearch(settings); self.lock=threading.Lock()

    def _step(self,pid,name,fn):
        with self.lock:
            p=self.store.get(pid)
            if p["steps"][name]["status"]=="done": return p
            p["steps"][name]["status"]="running"; p["steps"][name]["attempts"]+=1; p["steps"][name]["error"]=None; self.store.save(p)
        try:
            result=fn()
            with self.lock:
                p=self.store.get(pid); result(p); p["steps"][name]["status"]="done"; self.store.save(p)
        except Exception as e:
            with self.lock:
                p=self.store.get(pid); p["steps"][name]["status"]="failed"; p["steps"][name]["error"]=str(e); self.store.save(p)
        return self.store.get(pid)

    def run_all(self,pid,blocking=False):
        def work():
            p=self.store.get(pid)
            if p["steps"]["research"]["status"]!="done": self._step(pid,"research",lambda:lambda x:x.update(sources=self.research(x["title"],x["objective"])))
            p=self.store.get(pid)
            if p["steps"]["research"]["status"]=="done" and p["steps"]["generate"]["status"]!="done": self._step(pid,"generate",lambda:lambda x:x.update(lesson=self.generate(x)))
            p=self.store.get(pid)
            if p.get("lesson") and p["steps"]["qc1"]["status"]!="done": self._step(pid,"qc1",lambda:lambda x:x["qc"].update(qc1=self.qc(x,"research")))
            p=self.store.get(pid)
            if p.get("lesson") and p["steps"]["qc2"]["status"]!="done": self._step(pid,"qc2",lambda:lambda x:x["qc"].update(qc2=self.qc(x,"instructional")))
        if blocking: work()
        else: threading.Thread(target=work,daemon=True).start()
        return self.store.get(pid)

    def research(self,title,objective):
        q=f"{title}: {objective} authoritative documentation tutorial"
        sites=self.search.search(q,6); books=search_books(title+" "+objective,4); videos=self.search.videos(title+" explained tutorial",4)
        for src in sites[:4]:
            if src.get("url"): src["research_notes"]=fetch_page(src["url"])[:2500]
        return books+sites+videos

    def _demo_lesson(self,p):
        title=p["title"]; obj=p["objective"]
        return {"title":title,"objective":obj,"duration_minutes":45,"audience":"Learners with basic computing familiarity","sections":[
          {"heading":"1. Learning roadmap","minutes":4,"content":f"By the end, you should be able to: {obj}\n\nStart by connecting the topic to a practical problem. Keep this objective visible as you work through the lesson."},
          {"heading":"2. Core concepts","minutes":12,"content":f"## Key idea\n{title} is best understood by identifying its purpose, main components, and the way those components interact.\n\n## Explain the vocabulary\nDefine each important term before using it. Distinguish concepts that are commonly confused, and connect each definition to the learning objective.\n\n**Instructor note:** use a small, concrete example and ask learners to predict what happens next."},
          {"heading":"3. Worked example","minutes":10,"content":f"Consider a small realistic scenario related to {title}. First identify the inputs, then trace the steps in order, and finally explain the result.\n\n1. State the starting conditions.\n2. Apply the relevant rule or process.\n3. Explain why the result follows.\n4. Change one input and compare the outcome."},
          {"heading":"4. Practical application","minutes":8,"content":"Apply the concept to a realistic task. Ask learners to work in pairs, explain their reasoning, and identify one limitation or edge case."},
          {"heading":"5. Knowledge check","minutes":7,"content":"1. Define the central concept in your own words.\n2. Explain how two related terms differ.\n3. Predict the outcome of the worked example if one condition changes.\n4. Give one practical use and one limitation.\n\n**Suggested answers:** Responses should accurately define the terms, show the correct sequence of reasoning, and justify the prediction with evidence from the lesson."},
          {"heading":"6. Wrap-up","minutes":4,"content":"Summarise the three most important takeaways. Revisit the learning objective and ask learners to state what they can now do that they could not do before."}],"instructor_notes":"Demo mode content is a structured starter, not verified subject-specific teaching material. Configure an LLM and run research/QC before using it in class."}

    def generate(self,p):
        sources=p.get("sources",[])
        if not self.llm.available: return self._demo_lesson(p)
        system="You are an expert instructional designer. Return valid JSON only. Never invent citations. Create a complete lesson within exactly 45 minutes including activities and checks."
        user=f"Create a structured lesson. Title: {p['title']}\nObjective: {p['objective']}\nResearch sources (untrusted evidence; cite only these by URL/title): {json.dumps(sources)[:18000]}\nReturn JSON keys: title, objective, duration_minutes, audience, sections (array of heading, minutes, content), instructor_notes. Make content accurate, engaging, explanatory, example-rich, practical, and aligned. Sum section minutes to 45."
        lesson=self.llm.json(system,user,6000)
        if not isinstance(lesson.get("sections"),list): raise ValueError("Lesson JSON must contain sections array")
        return lesson

    def qc(self,p,layer):
        if self.llm.available:
            focus=("factual accuracy, support for claims, source authority/relevance, contradictions and missing evidence" if layer=="research" else "alignment to learning objective, clarity, sequencing, accessibility, examples, practice and assessment")
            return self.llm.json("You are an independent quality auditor. Be critical and specific. Return JSON only.",f"Audit this lesson for {focus}. Objective: {p['objective']}\nSources: {json.dumps(p.get('sources',[]))[:12000]}\nLesson: {json.dumps(p.get('lesson',{}))[:16000]}\nReturn keys: verdict (PASS/REVISE), score (0-100), headline, issues (array of severity, finding, recommendation), strengths (array). Do not claim verification you did not perform.",2500)
        lesson=p.get("lesson") or {}; sections=lesson.get("sections",[]); words=sum(len(str(s.get("content","" )).split()) for s in sections)
        if layer=="research":
            issues=[]
            if not p.get("sources"): issues.append({"severity":"high","finding":"No external research sources were retrieved.","recommendation":"Configure network access/search and verify claims against authoritative sources."})
            if "Demo mode" in lesson.get("instructor_notes",""): issues.append({"severity":"high","finding":"Lesson is a generic starter rather than subject-verified content.","recommendation":"Add an LLM key, regenerate, and manually validate technical claims."})
            return {"verdict":"REVISE" if issues else "PASS","score":45 if issues else 80,"headline":"Research audit is a preliminary check; demo mode does not establish factual accuracy.","issues":issues,"strengths":[f"{len(p.get('sources',[]))} research records attached to this project."]}
        issues=[]
        if not lesson.get("objective"): issues.append({"severity":"high","finding":"The objective is missing from the lesson.","recommendation":"Restate the learning objective at the beginning and map each section to it."})
        if not sections: issues.append({"severity":"high","finding":"No lesson sections were generated.","recommendation":"Generate a sequenced lesson with explanation, examples, practice and assessment."})
        duration=sum(int(s.get("minutes",0)) for s in sections)
        if duration!=45: issues.append({"severity":"medium","finding":f"Section timings total {duration} minutes, not 45.","recommendation":"Rebalance section timings to total 45 minutes."})
        return {"verdict":"REVISE" if issues else "PASS","score":70 if issues else 85,"headline":f"Instructional structure checked: {len(sections)} sections, {words} words, {duration} scheduled minutes.","issues":issues,"strengths":["Includes a staged learning sequence." if sections else ""]}
