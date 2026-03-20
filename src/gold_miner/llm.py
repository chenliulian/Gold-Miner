from __future__ import annotations

import json
import time
import requests
from typing import Any, Dict, List, Optional

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig


class LLMError(RuntimeError):
    pass


class OpenAICompatibleClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 60,
        enable_circuit_breaker: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._supports_json_mode: Optional[bool] = None

        # Circuit breaker for LLM API calls
        if enable_circuit_breaker:
            # Try to load config from environment
            try:
                from .config import Config
                config = Config.from_env()
                failure_threshold = config.circuit_breaker_failure_threshold
                recovery_timeout = config.circuit_breaker_recovery_timeout
            except Exception:
                # Fallback to defaults
                failure_threshold = 5
                recovery_timeout = 30.0

            self._circuit_breaker = CircuitBreaker(
                name="llm_api",
                config=CircuitBreakerConfig(
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                    expected_exception=(requests.RequestException, LLMError),
                ),
            )
        else:
            self._circuit_breaker = None

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        enforce_json: bool = False,
        retries: int = 2,
    ) -> str:
        """Send chat request to LLM with circuit breaker protection."""
        # Use circuit breaker if available
        if self._circuit_breaker:
            return self._circuit_breaker.call(
                self._chat_with_retry,
                messages,
                temperature,
                enforce_json,
                retries,
            )
        else:
            return self._chat_with_retry(
                messages,
                temperature,
                enforce_json,
                retries,
            )

    def _chat_with_retry(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        enforce_json: bool = False,
        retries: int = 2,
    ) -> str:
        """Internal method with retry logic."""
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

        # 如果已知后端不支持 JSON mode，且强制要求 JSON，则在 prompt 中添加提示
        if enforce and self._supports_json_mode is False:
            messages = self._add_json_instruction(messages)

        while attempt <= retries:
            try:
                resp = _request(enforce)
                if resp.status_code < 400:
                    data = resp.json()
                    try:
                        content = data["choices"][0]["message"]["content"]
                        # 如果强制要求 JSON，验证返回内容是否为有效 JSON
                        if enforce_json:
                            content = self._validate_and_fix_json(content)
                        return content
                    except Exception as exc:  # noqa: BLE001
                        raise LLMError(f"Unexpected LLM response: {data}") from exc
                last_error = f"{resp.status_code}: {resp.text}"
                # If the backend doesn't support response_format, retry without it once.
                if enforce and resp.status_code == 400:
                    self._supports_json_mode = False
                    enforce = False
                    # 在 prompt 中添加 JSON 格式要求
                    messages = self._add_json_instruction(messages)
                else:
                    time.sleep(0.5 * (2**attempt))
            except requests.exceptions.ReadTimeout as e:
                last_error = f"Read timeout: {e}"
                print(f"[LLM] Request timeout (attempt {attempt + 1}/{retries + 1}), retrying...")
                time.sleep(1.0 * (2**attempt))
            except requests.exceptions.RequestException as e:
                last_error = f"Request error: {e}"
                print(f"[LLM] Request error (attempt {attempt + 1}/{retries + 1}): {e}")
                time.sleep(0.5 * (2**attempt))
            attempt += 1

        raise LLMError(f"LLM error after {retries + 1} attempts: {last_error}")
    
    def _add_json_instruction(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """在 system message 中添加 JSON 格式要求"""
        messages = list(messages)  # 复制列表
        if messages and messages[0].get("role") == "system":
            original_content = messages[0]["content"]
            json_instruction = "\n\nIMPORTANT: You MUST respond with a valid JSON object only, no extra text, no markdown formatting."
            messages[0] = {
                "role": "system",
                "content": original_content + json_instruction
            }
        return messages
    
    def _validate_and_fix_json(self, content: str) -> str:
        """验证并尝试修复 JSON 内容"""
        content = content.strip()
        
        # 尝试直接解析
        try:
            json.loads(content)
            return content
        except json.JSONDecodeError:
            pass
        
        # 移除可能的 markdown 代码块标记
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # 再次尝试解析
        try:
            json.loads(content)
            return content
        except json.JSONDecodeError as e:
            # 如果仍然无法解析，记录警告但返回原始内容
            # 让调用方决定如何处理
            print(f"[Warning] LLM returned invalid JSON: {e}")
            return content
