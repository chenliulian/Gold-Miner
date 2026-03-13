from __future__ import annotations

import json
import time
import requests
from typing import Any, Dict, List, Optional


class LLMError(RuntimeError):
    pass


class OpenAICompatibleClient:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        enforce_json: bool = False,
        retries: int = 2,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        def _request(enforce: bool) -> requests.Response:
            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            if enforce:
                payload["response_format"] = {"type": "json_object"}
            return requests.post(
                url, headers=headers, data=json.dumps(payload), timeout=self.timeout
            )

        attempt = 0
        last_error: Optional[str] = None
        enforce = enforce_json
        while attempt <= retries:
            resp = _request(enforce)
            if resp.status_code < 400:
                data = resp.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except Exception as exc:  # noqa: BLE001
                    raise LLMError(f"Unexpected LLM response: {data}") from exc
            last_error = f"{resp.status_code}: {resp.text}"
            # If the backend doesn't support response_format, retry without it once.
            if enforce and resp.status_code == 400:
                enforce = False
            else:
                time.sleep(0.5 * (2**attempt))
            attempt += 1

        raise LLMError(f"LLM error {last_error}")
