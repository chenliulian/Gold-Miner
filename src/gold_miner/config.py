from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    llm_base_url: str
    llm_api_key: str
    llm_model: str

    odps_access_id: str
    odps_access_key: str
    odps_project: str
    odps_endpoint: str

    agent_max_steps: int = 6
    memory_path: str = "./memory/memory.json"
    reports_dir: str = "./reports"

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls(
            llm_base_url=os.getenv("LLM_BASE_URL", "").strip(),
            llm_api_key=os.getenv("LLM_API_KEY", "").strip(),
            llm_model=os.getenv("LLM_MODEL", "").strip(),
            odps_access_id=os.getenv("ODPS_ACCESS_ID", "").strip(),
            odps_access_key=os.getenv("ODPS_ACCESS_KEY", "").strip(),
            odps_project=os.getenv("ODPS_PROJECT", "").strip(),
            odps_endpoint=os.getenv("ODPS_ENDPOINT", "").strip(),
            agent_max_steps=int(os.getenv("AGENT_MAX_STEPS", "6")),
            memory_path=os.getenv("MEMORY_PATH", "./memory/memory.json"),
            reports_dir=os.getenv("REPORTS_DIR", "./reports"),
        )

    def validate(self) -> None:
        missing = []
        if not self.llm_base_url:
            missing.append("LLM_BASE_URL")
        if not self.llm_api_key:
            missing.append("LLM_API_KEY")
        if not self.llm_model:
            missing.append("LLM_MODEL")
        if not self.odps_access_id:
            missing.append("ODPS_ACCESS_ID")
        if not self.odps_access_key:
            missing.append("ODPS_ACCESS_KEY")
        if not self.odps_project:
            missing.append("ODPS_PROJECT")
        if not self.odps_endpoint:
            missing.append("ODPS_ENDPOINT")
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")
