import os
import tempfile
from unittest.mock import patch

import pytest

from gold_miner.config import Config


class TestConfig:
    def test_from_env_with_valid_values(self):
        with patch("gold_miner.config.load_dotenv"):
            with patch.dict(
                os.environ,
                {
                    "LLM_BASE_URL": "https://api.example.com",
                    "LLM_API_KEY": "test-key",
                    "LLM_MODEL": "gpt-4",
                    "ODPS_ACCESS_ID": "test-id",
                    "ODPS_ACCESS_KEY": "test-key",
                    "ODPS_PROJECT": "test-project",
                    "ODPS_ENDPOINT": "https://test.odps.aliyun.com",
                },
            ):
                config = Config.from_env()

                assert config.llm_base_url == "https://api.example.com"
                assert config.llm_api_key == "test-key"
                assert config.llm_model == "gpt-4"
                assert config.odps_access_id == "test-id"
                assert config.odps_access_key == "test-key"
                assert config.odps_project == "test-project"
                assert config.odps_endpoint == "https://test.odps.aliyun.com"
                # Default value from Config class (may be overridden by .env file)
                assert config.memory_path == "./memory/memory.json"
                assert config.reports_dir == "./reports"

    def test_from_env_with_custom_values(self):
        with patch("gold_miner.config.load_dotenv"):
            with patch.dict(
                os.environ,
                {
                    "LLM_BASE_URL": "https://api.example.com",
                    "LLM_API_KEY": "test-key",
                    "LLM_MODEL": "gpt-4",
                    "ODPS_ACCESS_ID": "test-id",
                    "ODPS_ACCESS_KEY": "test-key",
                    "ODPS_PROJECT": "test-project",
                    "ODPS_ENDPOINT": "https://test.odps.aliyun.com",
                    "AGENT_MAX_STEPS": "10",
                    "MEMORY_PATH": "./custom/memory.json",
                    "REPORTS_DIR": "./custom/reports",
                },
            ):
                config = Config.from_env()

                assert config.agent_max_steps == 10
                assert config.memory_path == "./custom/memory.json"
                assert config.reports_dir == "./custom/reports"

    def test_from_env_with_whitespace(self):
        with patch("gold_miner.config.load_dotenv"):
            with patch.dict(
                os.environ,
                {
                    "LLM_BASE_URL": "  https://api.example.com  ",
                    "LLM_API_KEY": "  test-key  ",
                    "LLM_MODEL": "  gpt-4  ",
                    "ODPS_ACCESS_ID": "  test-id  ",
                    "ODPS_ACCESS_KEY": "  test-key  ",
                    "ODPS_PROJECT": "  test-project  ",
                    "ODPS_ENDPOINT": "  https://test.odps.aliyun.com  ",
                },
            ):
                config = Config.from_env()

                assert config.llm_base_url == "https://api.example.com"
                assert config.llm_api_key == "test-key"
                assert config.llm_model == "gpt-4"

    def test_validate_success(self):
        with patch("gold_miner.config.load_dotenv"):
            with patch.dict(
                os.environ,
                {
                    "LLM_BASE_URL": "https://api.example.com",
                    "LLM_API_KEY": "test-key",
                    "LLM_MODEL": "gpt-4",
                    "ODPS_ACCESS_ID": "test-id",
                    "ODPS_ACCESS_KEY": "test-key",
                    "ODPS_PROJECT": "test-project",
                    "ODPS_ENDPOINT": "https://test.odps.aliyun.com",
                },
            ):
                config = Config.from_env()
                config.validate()

    def test_validate_missing_llm_base_url(self):
        with patch("gold_miner.config.load_dotenv"):
            with patch.dict(
                os.environ,
                {
                    "LLM_API_KEY": "test-key",
                    "LLM_MODEL": "gpt-4",
                    "ODPS_ACCESS_ID": "test-id",
                    "ODPS_ACCESS_KEY": "test-key",
                    "ODPS_PROJECT": "test-project",
                    "ODPS_ENDPOINT": "https://test.odps.aliyun.com",
                },
                clear=True,
            ):
                config = Config.from_env()

                with pytest.raises(ValueError) as exc_info:
                    config.validate()

                assert "LLM_BASE_URL" in str(exc_info.value)

    def test_validate_missing_llm_api_key(self):
        with patch("gold_miner.config.load_dotenv"):
            with patch.dict(
                os.environ,
                {
                    "LLM_BASE_URL": "https://api.example.com",
                    "LLM_MODEL": "gpt-4",
                    "ODPS_ACCESS_ID": "test-id",
                    "ODPS_ACCESS_KEY": "test-key",
                    "ODPS_PROJECT": "test-project",
                    "ODPS_ENDPOINT": "https://test.odps.aliyun.com",
                },
                clear=True,
            ):
                config = Config.from_env()

                with pytest.raises(ValueError) as exc_info:
                    config.validate()

                assert "LLM_API_KEY" in str(exc_info.value)

    def test_validate_missing_llm_model(self):
        with patch("gold_miner.config.load_dotenv"):
            with patch.dict(
                os.environ,
                {
                    "LLM_BASE_URL": "https://api.example.com",
                    "LLM_API_KEY": "test-key",
                    "ODPS_ACCESS_ID": "test-id",
                    "ODPS_ACCESS_KEY": "test-key",
                    "ODPS_PROJECT": "test-project",
                    "ODPS_ENDPOINT": "https://test.odps.aliyun.com",
                },
                clear=True,
            ):
                config = Config.from_env()

                with pytest.raises(ValueError) as exc_info:
                    config.validate()

                assert "LLM_MODEL" in str(exc_info.value)

    def test_validate_missing_odps_access_id(self):
        with patch("gold_miner.config.load_dotenv"):
            with patch.dict(
                os.environ,
                {
                    "LLM_BASE_URL": "https://api.example.com",
                    "LLM_API_KEY": "test-key",
                    "LLM_MODEL": "gpt-4",
                    "ODPS_ACCESS_KEY": "test-key",
                    "ODPS_PROJECT": "test-project",
                    "ODPS_ENDPOINT": "https://test.odps.aliyun.com",
                },
                clear=True,
            ):
                config = Config.from_env()

                with pytest.raises(ValueError) as exc_info:
                    config.validate()

                assert "ODPS_ACCESS_ID" in str(exc_info.value)

    def test_validate_missing_multiple(self):
        with patch("gold_miner.config.load_dotenv"):
            with patch.dict(
                os.environ,
                {
                    "LLM_BASE_URL": "https://api.example.com",
                    "ODPS_PROJECT": "test-project",
                },
                clear=True,
            ):
                config = Config.from_env()

                with pytest.raises(ValueError) as exc_info:
                    config.validate()

                error_msg = str(exc_info.value)
                assert "LLM_API_KEY" in error_msg
                assert "LLM_MODEL" in error_msg
                assert "ODPS_ACCESS_ID" in error_msg
