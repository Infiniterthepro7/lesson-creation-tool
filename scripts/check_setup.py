from dotenv import load_dotenv
load_dotenv()
"""Integration pre-flight check. Run: python scripts/check_setup.py"""
from lessontool.config import Settings
from lessontool.llm import LLMClient
from lessontool.search import WebSearch, search_books, oembed

def main():
    s=Settings.from_env(); print('Configuration warnings:'); [print('-',x) for x in s.problems()]
    llm=LLMClient(s)
    if llm.available:
        print('LLM:',llm.complete('Be concise.','Reply with exactly: ready',max_tokens=20))
    else: print('LLM: skipped (demo mode; configure a key for live generation/QC)')
    ws=WebSearch(s)
    print('Web results:',len(ws.search('HTTP request methods MDN',3)))
    print('Video results:',len(ws.videos('HTTP explained tutorial',3)))
    print('Book results:',len(search_books('HTTP protocol',3)))
    print('YouTube oEmbed:',bool(oembed('https://www.youtube.com/watch?v=dQw4w9WgXcQ')))
if __name__=='__main__': main()
