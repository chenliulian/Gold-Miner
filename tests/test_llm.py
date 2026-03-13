import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from gold_miner.llm import LLMError, OpenAICompatibleClient


class TestOpenAICompatibleClient:
    def test_init(self):
        client = OpenAICompatibleClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-4",
        )
        assert client.base_url == "https://api.example.com"
        assert client.api_key == "test-key"
        assert client.model == "gpt-4"
        assert client.timeout == 60

    def test_init_with_custom_timeout(self):
        client = OpenAICompatibleClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-4",
            timeout=120,
        )
        assert client.timeout == 120

    def test_init_strips_trailing_slash(self):
        client = OpenAICompatibleClient(
            base_url="https://api.example.com/",
            api_key="test-key",
            model="gpt-4",
        )
        assert client.base_url == "https://api.example.com"

    @patch("gold_miner.llm.requests.post")
    def test_chat_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"action": "run_sql", "sql": "SELECT 1"}'}}]
        }
        mock_post.return_value = mock_response

        client = OpenAICompatibleClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-4",
        )
        messages = [{"role": "user", "content": "Hello"}]
        result = client.chat(messages)

        assert result == '{"action": "run_sql", "sql": "SELECT 1"}'
        mock_post.assert_called_once()

    @patch("gold_miner.llm.requests.post")
    def test_chat_with_temperature(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }
        mock_post.return_value = mock_response

        client = OpenAICompatibleClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-4",
        )
        messages = [{"role": "user", "content": "Hello"}]
        client.chat(messages, temperature=0.5)

        call_args = mock_post.call_args
        payload = json.loads(call_args.kwargs["data"])
        assert payload["temperature"] == 0.5

    @patch("gold_miner.llm.requests.post")
    def test_chat_with_enforce_json(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"action": "final"}'}}]
        }
        mock_post.return_value = mock_response

        client = OpenAICompatibleClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-4",
        )
        messages = [{"role": "user", "content": "Hello"}]
        client.chat(messages, enforce_json=True)

        call_args = mock_post.call_args
        payload = json.loads(call_args.kwargs["data"])
        assert payload["response_format"] == {"type": "json_object"}

    @patch("gold_miner.llm.requests.post")
    def test_chat_retry_on_500_error(self, mock_post):
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.text = "Internal Server Error"

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "choices": [{"message": {"content": "success"}}]
        }

        mock_post.side_effect = [mock_response_500, mock_response_200]

        client = OpenAICompatibleClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-4",
        )
        messages = [{"role": "user", "content": "Hello"}]
        result = client.chat(messages, retries=1)

        assert result == "success"
        assert mock_post.call_count == 2

    @patch("gold_miner.llm.requests.post")
    def test_chat_retry_without_response_format_on_400(self, mock_post):
        mock_response_400 = MagicMock()
        mock_response_400.status_code = 400
        mock_response_400.text = "Bad Request"

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "choices": [{"message": {"content": "success"}}]
        }

        mock_post.side_effect = [mock_response_400, mock_response_200]

        client = OpenAICompatibleClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-4",
        )
        messages = [{"role": "user", "content": "Hello"}]
        result = client.chat(messages, enforce_json=True, retries=1)

        assert result == "success"
        assert mock_post.call_count == 2

    @patch("gold_miner.llm.requests.post")
    def test_chat_raises_llm_error_on_exhausted_retries(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        client = OpenAICompatibleClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-4",
        )
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(LLMError) as exc_info:
            client.chat(messages, retries=2)

        assert "LLM error" in str(exc_info.value)

    @patch("gold_miner.llm.requests.post")
    def test_chat_raises_llm_error_on_unexpected_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "format"}
        mock_post.return_value = mock_response

        client = OpenAICompatibleClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-4",
        )
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(LLMError) as exc_info:
            client.chat(messages)

        assert "Unexpected LLM response" in str(exc_info.value)


class TestLLMError:
    def test_llm_error_is_runtime_error(self):
        error = LLMError("test error")
        assert isinstance(error, RuntimeError)

    def test_llm_error_message(self):
        error = LLMError("test error message")
        assert str(error) == "test error message"
