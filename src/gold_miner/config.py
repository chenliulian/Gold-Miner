from __future__ import annotations

import os
import secrets
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
    odps_quota: str = ""  # ODPS 计算资源配额，如 "quota_name" 或 "quota_name/nickname"

    agent_max_steps: int = 6
    memory_path: str = "./memory/state.json"
    memory_summary_path: str = "./memory/summary.md"
    reports_dir: str = "./reports"

    # Security settings
    session_secret: str = ""
    enable_sql_validation: bool = True
    max_sql_length: int = 50000
    request_rate_limit: str = "100 per minute"

    # Agent Pool settings
    agent_pool_min_size: int = 2
    agent_pool_max_size: int = 10
    agent_pool_max_idle_time: int = 3600

    # Rate limiting settings
    rate_limit_default_per_minute: int = 60
    rate_limit_chat_per_minute: int = 10

    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 30.0

    # Scheduler settings
    scheduler_auto_start: bool = False
    scheduler_review_interval_hours: int = 24
    scheduler_session_review_hours: int = 1

    # Authentication settings
    jwt_secret: str = ""
    token_expires_hours: int = 8

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
            odps_quota=os.getenv("ODPS_QUOTA", "").strip(),
            agent_max_steps=int(os.getenv("AGENT_MAX_STEPS", "6")),
            memory_path=os.getenv("MEMORY_PATH", "./memory/state.json"),
            memory_summary_path=os.getenv("MEMORY_SUMMARY_PATH", "./memory/summary.md"),
            reports_dir=os.getenv("REPORTS_DIR", "./reports"),
            session_secret=os.getenv("SESSION_SECRET", "").strip(),
            enable_sql_validation=os.getenv("ENABLE_SQL_VALIDATION", "true").lower() == "true",
            max_sql_length=int(os.getenv("MAX_SQL_LENGTH", "50000")),
            request_rate_limit=os.getenv("REQUEST_RATE_LIMIT", "100 per minute"),
            # Agent Pool settings
            agent_pool_min_size=int(os.getenv("AGENT_POOL_MIN_SIZE", "2")),
            agent_pool_max_size=int(os.getenv("AGENT_POOL_MAX_SIZE", "10")),
            agent_pool_max_idle_time=int(os.getenv("AGENT_POOL_MAX_IDLE_TIME", "3600")),
            # Rate limiting settings
            rate_limit_default_per_minute=int(os.getenv("RATE_LIMIT_DEFAULT_PER_MINUTE", "60")),
            rate_limit_chat_per_minute=int(os.getenv("RATE_LIMIT_CHAT_PER_MINUTE", "10")),
            # Circuit breaker settings
            circuit_breaker_failure_threshold=int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")),
            circuit_breaker_recovery_timeout=float(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30.0")),
            # Scheduler settings
            scheduler_auto_start=os.getenv("SCHEDULER_AUTO_START", "false").lower() == "true",
            scheduler_review_interval_hours=int(os.getenv("SCHEDULER_REVIEW_INTERVAL_HOURS", "24")),
            scheduler_session_review_hours=int(os.getenv("SCHEDULER_SESSION_REVIEW_HOURS", "1")),
            # Authentication settings
            jwt_secret=os.getenv("JWT_SECRET", "").strip(),
            token_expires_hours=int(os.getenv("TOKEN_EXPIRES_HOURS", "8")),
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
    
    def validate_security(self) -> None:
        """Validate security-related configuration."""
        if not self.session_secret:
            raise ValueError(
                "SESSION_SECRET is required for security. "
                "Please set a strong secret key (at least 32 characters) in your .env file. "
                "You can generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        
        if len(self.session_secret) < 32:
            raise ValueError(
                f"SESSION_SECRET must be at least 32 characters long (current: {len(self.session_secret)}). "
                "Please use a stronger secret key."
            )
        
        # Check for common weak secrets
        weak_secrets = [
            "gold-miner-secret-key",
            "secret",
            "password",
            "123456",
            "admin",
            "default",
        ]
        if self.session_secret.lower() in weak_secrets:
            raise ValueError(
                f"SESSION_SECRET '{self.session_secret}' is too weak and easily guessable. "
                "Please use a cryptographically secure random string."
            )


def generate_secure_secret() -> str:
    """Generate a cryptographically secure session secret."""
    return secrets.token_hex(32)
