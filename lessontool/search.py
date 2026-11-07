"""Research adapters. Search is best-effort; source metadata is retained for citation."""
import requests
from bs4 import BeautifulSoup

class WebSearch:
    def __init__(self, settings): self.s=settings

    def search(self, query, limit=6):
        if self.s.search_provider == "tavily" and self.s.tavily_key:
            try:
                r=requests.post("https://api.tavily.com/search", json={"api_key":self.s.tavily_key,"query":query,"max_results":limit,"search_depth":"basic"}, timeout=25); r.raise_for_status()
                return [{"title":x.get("title",""),"url":x.get("url",""),"snippet":x.get("content",""),"kind":"Website"} for x in r.json().get("results",[])]
            except requests.RequestException: pass
        try:
            from ddgs import DDGS
            rows=DDGS().text(query, max_results=limit)
            return [{"title":x.get("title",""),"url":x.get("href",x.get("url","")),"snippet":x.get("body",""),"kind":"Website"} for x in rows]
        except Exception:
            return []

    def videos(self, query, limit=4):
        try:
            from ddgs import DDGS
            rows=DDGS().videos(query, max_results=limit)
            out=[]
            for x in rows:
                url=x.get("content",x.get("url", "")) or x.get("embed_url","")
                out.append({"title":x.get("title","YouTube learning resource"),"url":url,"snippet":x.get("description", ""),"kind":"Video"})
            return out
        except Exception: return []

def fetch_page(url, timeout=12):
    if not url.startswith(("http://","https://")): return ""
    try:
        r=requests.get(url,headers={"User-Agent":"LessonResearchTool/1.0"},timeout=timeout); r.raise_for_status()
        soup=BeautifulSoup(r.text,"lxml")
        for tag in soup(["script","style","nav","footer","header"]): tag.decompose()
        return " ".join(soup.get_text(" ",strip=True).split())[:7000]
    except requests.RequestException: return ""

def search_books(query, limit=5):
    try:
        r=requests.get("https://www.googleapis.com/books/v1/volumes",params={"q":query,"maxResults":limit},timeout=15); r.raise_for_status()
        out=[]
        for item in r.json().get("items",[]):
            v=item.get("volumeInfo",{}); out.append({"title":v.get("title","Untitled book"),"authors":v.get("authors",[]),"url":v.get("infoLink", ""),"snippet":v.get("description", "")[:500],"kind":"Book"})
        return out
    except requests.RequestException: return []

def oembed(url):
    try:
        r=requests.get("https://www.youtube.com/oembed",params={"url":url,"format":"json"},timeout=10); r.raise_for_status(); return r.json()
    except requests.RequestException: return None
