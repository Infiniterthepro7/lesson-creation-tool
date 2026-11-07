from dataclasses import dataclass
import os
from pathlib import Path

@dataclass
class Settings:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    openai_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_key: str = ""
    search_provider: str = "ddgs"
    tavily_key: str = ""
    youtube_key: str = ""
    data_dir: str = "./data"
    port: int = 5000
    lesson_minutes: int = 45

    @classmethod
    def from_env(cls):
        return cls(
            provider=os.getenv("LLM_PROVIDER", "openai").lower(),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            openai_key=os.getenv("OPENAI_API_KEY", ""),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            anthropic_key=os.getenv("ANTHROPIC_API_KEY", ""),
            search_provider=os.getenv("SEARCH_PROVIDER", "ddgs").lower(),
            tavily_key=os.getenv("TAVILY_API_KEY", ""),
            youtube_key=os.getenv("YOUTUBE_API_KEY", ""),
            data_dir=os.getenv("DATA_DIR", "./data"),
            port=int(os.getenv("PORT", "5000")),
            lesson_minutes=int(os.getenv("LESSON_MINUTES", "45")),
        )

    def problems(self):
        issues=[]
        if self.provider == "anthropic" and not self.anthropic_key:
            issues.append("ANTHROPIC_API_KEY is missing; generation will use transparent demo mode.")
        if self.provider == "openai" and not self.openai_key:
            issues.append("OPENAI_API_KEY is missing; generation will use transparent demo mode.")
        if self.search_provider == "tavily" and not self.tavily_key:
            issues.append("TAVILY_API_KEY is missing; web research will fall back to DuckDuckGo.")
        return issues
