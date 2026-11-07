import json
import requests

class LLMError(RuntimeError): pass

class LLMClient:
    def __init__(self, settings): self.s=settings

    @property
    def available(self):
        return bool(self.s.anthropic_key if self.s.provider == "anthropic" else self.s.openai_key)

    def complete(self, system, user, max_tokens=5000, temperature=0.2):
        if not self.available:
            raise LLMError("No LLM API key configured. Add one to .env or use demo mode.")
        try:
            if self.s.provider == "anthropic":
                r=requests.post("https://api.anthropic.com/v1/messages", headers={"x-api-key":self.s.anthropic_key,"anthropic-version":"2023-06-01","content-type":"application/json"}, json={"model":self.s.model,"max_tokens":max_tokens,"temperature":temperature,"system":system,"messages":[{"role":"user","content":user}]}, timeout=120)
                r.raise_for_status(); return "\n".join(x.get("text","") for x in r.json().get("content",[]))
            r=requests.post(self.s.openai_base_url+"/chat/completions", headers={"Authorization":"Bearer "+self.s.openai_key,"Content-Type":"application/json"}, json={"model":self.s.model,"temperature":temperature,"max_tokens":max_tokens,"messages":[{"role":"system","content":system},{"role":"user","content":user}]}, timeout=120)
            r.raise_for_status(); return r.json()["choices"][0]["message"]["content"]
        except requests.RequestException as e: raise LLMError(f"LLM request failed: {e}") from e

    def json(self, system, user, max_tokens=5000):
        raw=self.complete(system, user, max_tokens=max_tokens)
        raw=raw.strip()
        if raw.startswith("```"):
            raw=raw.split("\n",1)[1].rsplit("```",1)[0]
        try: return json.loads(raw)
        except json.JSONDecodeError as e: raise LLMError(f"Model returned invalid JSON: {e}") from e
