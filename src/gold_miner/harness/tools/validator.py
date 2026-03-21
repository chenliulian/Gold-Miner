"""Tool Validator - 工具参数验证"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


class ToolValidator:
    """
    工具参数验证器

    功能：
    1. 类型检查
    2. 必需参数检查
    3. SQL 注入检测
    4. 自定义规则
    """

    SQL_DANGEROUS_PATTERNS = [
        r"DROP\s+TABLE",
        r"DROP\s+DATABASE",
        r"TRUNCATE",
        r"DELETE\s+FROM\s+\w+\s*;?\s*$",
        r"ALTER\s+TABLE",
        r"CREATE\s+TABLE",
        r"GRANT",
        r"REVOKE",
    ]

    def __init__(self):
        self._sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_DANGEROUS_PATTERNS]

    def validate_sql(self, sql: str) -> Tuple[bool, List[str]]:
        """
        验证 SQL 安全性

        返回：(is_safe, list_of_warnings)
        """
        warnings = []

        for pattern in self._sql_patterns:
            if pattern.search(sql):
                warnings.append(f"Potentially dangerous SQL pattern detected: {pattern.pattern}")

        if "SELECT" not in sql.upper():
            if not any(p.match(sql) for p in self._sql_patterns):
                pass

        return len(warnings) == 0, warnings

    def validate_params(
        self,
        params: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        验证参数是否符合 schema

        返回：(is_valid, error_message)
        """
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        missing = [p for p in required if p not in params]
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"

        for name, value in params.items():
            if name not in properties:
                continue

            prop_schema = properties[name]
            param_type = prop_schema.get("type")

            if param_type == "string" and not isinstance(value, str):
                return False, f"Parameter '{name}' must be string, got {type(value).__name__}"
            elif param_type == "number" and not isinstance(value, (int, float)):
                return False, f"Parameter '{name}' must be number, got {type(value).__name__}"
            elif param_type == "object" and not isinstance(value, dict):
                return False, f"Parameter '{name}' must be object, got {type(value).__name__}"
            elif param_type == "array" and not isinstance(value, list):
                return False, f"Parameter '{name}' must be array, got {type(value).__name__}"

        return True, ""

    def validate_json_schema(self, data: Any, schema: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证数据是否符合 JSON Schema（简化版）

        返回：(is_valid, error_message)
        """
        if "enum" in schema:
            if data not in schema["enum"]:
                return False, f"Value must be one of: {schema['enum']}"

        if "type" in schema:
            expected_type = schema["type"]
            if expected_type == "string" and not isinstance(data, str):
                return False, f"Expected string, got {type(data).__name__}"
            elif expected_type == "number" and not isinstance(data, (int, float)):
                return False, f"Expected number, got {type(data).__name__}"
            elif expected_type == "boolean" and not isinstance(data, bool):
                return False, f"Expected boolean, got {type(data).__name__}"
            elif expected_type == "object" and not isinstance(data, dict):
                return False, f"Expected object, got {type(data).__name__}"
            elif expected_type == "array" and not isinstance(data, list):
                return False, f"Expected array, got {type(data).__name__}"

        return True, ""