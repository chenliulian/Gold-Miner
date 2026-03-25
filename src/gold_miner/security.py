"""Security utilities for SQL validation and input sanitization."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set, Tuple


class SQLValidationError(Exception):
    """Raised when SQL validation fails."""
    pass


class RiskLevel(Enum):
    """Risk level for SQL operations."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of SQL validation."""
    is_valid: bool
    risk_level: RiskLevel
    errors: List[str]
    warnings: List[str]


class SQLValidator:
    """SQL statement validator for preventing injection attacks."""

    # Forbidden keywords that are not allowed in any context
    FORBIDDEN_KEYWORDS: Set[str] = {
        'drop', 'truncate', 'delete', 'alter', 'create',
        'grant', 'revoke', 'commit', 'rollback',
    }

    # Dangerous keywords that require extra scrutiny
    DANGEROUS_KEYWORDS: Set[str] = {
        'insert', 'update', 'merge', 'load', 'unload',
    }

    # Allowed query types
    ALLOWED_STATEMENT_TYPES: Set[str] = {
        'select', 'with', 'desc', 'describe', 'show',
    }

    # Maximum allowed query length
    MAX_QUERY_LENGTH: int = 100000

    # Maximum allowed subquery depth
    MAX_SUBQUERY_DEPTH: int = 5

    def __init__(
        self,
        allowed_tables: Optional[List[str]] = None,
        allowed_projects: Optional[List[str]] = None,
        max_query_length: int = 100000,
    ):
        self.allowed_tables = set(allowed_tables or [])
        self.allowed_projects = set(allowed_projects or [])
        self.max_query_length = max_query_length

    def validate(self, sql: str) -> ValidationResult:
        """
        Validate a SQL statement.

        Args:
            sql: The SQL statement to validate

        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []

        # Basic checks
        if not sql or not sql.strip():
            errors.append("SQL statement is empty")
            return ValidationResult(False, RiskLevel.CRITICAL, errors, warnings)

        # Length check
        if len(sql) > self.max_query_length:
            errors.append(f"SQL statement exceeds maximum length of {self.max_query_length}")
            return ValidationResult(False, RiskLevel.CRITICAL, errors, warnings)

        # Normalize SQL for analysis
        normalized_sql = self._normalize_sql(sql)

        # Check for forbidden keywords
        forbidden_found = self._check_forbidden_keywords(normalized_sql)
        if forbidden_found:
            errors.append(f"Forbidden keywords detected: {', '.join(forbidden_found)}")
            return ValidationResult(False, RiskLevel.CRITICAL, errors, warnings)

        # Check statement type
        statement_type = self._get_statement_type(normalized_sql)
        if statement_type not in self.ALLOWED_STATEMENT_TYPES:
            errors.append(f"Statement type '{statement_type}' is not allowed. Only SELECT, WITH, DESC, SHOW are permitted")
            return ValidationResult(False, RiskLevel.HIGH, errors, warnings)

        # Check for dangerous keywords
        dangerous_found = self._check_dangerous_keywords(normalized_sql)
        if dangerous_found:
            warnings.append(f"Potentially dangerous keywords detected: {', '.join(dangerous_found)}")

        # Check subquery depth
        subquery_depth = self._calculate_subquery_depth(normalized_sql)
        if subquery_depth > self.MAX_SUBQUERY_DEPTH:
            errors.append(f"Subquery depth {subquery_depth} exceeds maximum of {self.MAX_SUBQUERY_DEPTH}")
            return ValidationResult(False, RiskLevel.HIGH, errors, warnings)

        # Check table access if whitelist is configured
        if self.allowed_tables:
            tables = self._extract_tables(normalized_sql)
            unauthorized = tables - self.allowed_tables
            if unauthorized:
                errors.append(f"Access to unauthorized tables: {', '.join(unauthorized)}")
                return ValidationResult(False, RiskLevel.HIGH, errors, warnings)

        # Check for SQL injection patterns
        injection_patterns = self._check_injection_patterns(sql)
        if injection_patterns:
            errors.append(f"Potential SQL injection patterns detected: {injection_patterns}")
            return ValidationResult(False, RiskLevel.CRITICAL, errors, warnings)

        # Determine risk level
        risk_level = self._calculate_risk_level(errors, warnings, normalized_sql)

        return ValidationResult(
            is_valid=len(errors) == 0,
            risk_level=risk_level,
            errors=errors,
            warnings=warnings,
        )

    def _normalize_sql(self, sql: str) -> str:
        """Normalize SQL for analysis."""
        # Remove comments
        sql = re.sub(r'--[^\n]*', ' ', sql)
        sql = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.DOTALL)
        # Normalize whitespace
        sql = ' '.join(sql.split())
        return sql.lower()

    def _check_forbidden_keywords(self, sql: str) -> List[str]:
        """Check for forbidden keywords."""
        found = []
        for keyword in self.FORBIDDEN_KEYWORDS:
            # Use word boundary to avoid partial matches
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql):
                found.append(keyword)
        return found

    def _check_dangerous_keywords(self, sql: str) -> List[str]:
        """Check for dangerous keywords."""
        found = []
        for keyword in self.DANGEROUS_KEYWORDS:
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql):
                found.append(keyword)
        return found

    def _get_statement_type(self, sql: str) -> str:
        """Get the type of SQL statement."""
        sql = sql.strip()
        # Remove leading parentheses for CTEs
        sql = re.sub(r'^\s*\(\s*', '', sql)
        match = re.match(r'^\s*(\w+)', sql)
        return match.group(1).lower() if match else 'unknown'

    def _calculate_subquery_depth(self, sql: str) -> int:
        """Calculate the maximum subquery nesting depth."""
        max_depth = 0
        current_depth = 0
        in_string = False
        string_char = None

        i = 0
        while i < len(sql):
            char = sql[i]

            # Handle strings
            if char in ("'", '"') and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                # Check for escaped quotes
                if i > 0 and sql[i-1] != '\\':
                    in_string = False
                    string_char = None
            elif not in_string:
                # Check for subquery keywords
                remaining = sql[i:]
                if remaining.startswith('(select') or remaining.startswith('( with'):
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif char == '(':
                    # Check if it's a subquery
                    next_chars = sql[i+1:i+10].strip().lower()
                    if next_chars.startswith('select') or next_chars.startswith('with'):
                        current_depth += 1
                        max_depth = max(max_depth, current_depth)
                elif char == ')':
                    current_depth = max(0, current_depth - 1)

            i += 1

        return max_depth

    def _extract_tables(self, sql: str) -> Set[str]:
        """Extract table names from SQL."""
        tables = set()

        # Pattern for table names (schema.table or just table)
        patterns = [
            r'\bfrom\s+(\w+(?:\.\w+)?)',
            r'\bjoin\s+(\w+(?:\.\w+)?)',
            r'\btable\s+(\w+(?:\.\w+)?)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.update(matches)

        return tables

    def _check_injection_patterns(self, sql: str) -> List[str]:
        """Check for common SQL injection patterns."""
        patterns = [
            (r';\s*\w+', 'Multiple statements'),
            (r'--\s*$', 'Comment injection'),
            (r'/\*.*?\*/', 'Block comment injection'),
            # UNION injection detection - only flag suspicious patterns like 'union select' without proper context
            # Normal UNION ALL / UNION between CTEs or subqueries is allowed
            (r'union\s+select\s+\d+', 'UNION injection'),
            (r'\bor\s+\d+=\d+', 'OR-based injection'),
            (r'\band\s+\d+=\d+', 'AND-based injection'),
            (r'\bexec\s*\(', 'EXEC injection'),
            (r'\bxp_', 'Extended stored procedure'),
        ]

        found = []
        normalized = sql.lower()
        for pattern, description in patterns:
            if re.search(pattern, normalized):
                found.append(description)

        return found

    def _calculate_risk_level(
        self,
        errors: List[str],
        warnings: List[str],
        sql: str,
    ) -> RiskLevel:
        """Calculate overall risk level."""
        if errors:
            return RiskLevel.CRITICAL

        if warnings:
            return RiskLevel.MEDIUM

        # Check complexity
        if len(sql) > 5000 or self._calculate_subquery_depth(sql) > 2:
            return RiskLevel.LOW

        return RiskLevel.SAFE


class InputSanitizer:
    """Input sanitization utilities."""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize a string input."""
        if not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value)}")

        # Remove null bytes
        value = value.replace('\x00', '')

        # Limit length
        if len(value) > max_length:
            value = value[:max_length]

        return value

    @staticmethod
    def sanitize_identifier(value: str) -> str:
        """Sanitize a SQL identifier (table/column name)."""
        if not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value)}")

        # Only allow alphanumeric, underscore, and dot
        if not re.match(r'^[\w\.]+$', value):
            raise ValueError(f"Invalid identifier: {value}")

        return value

    @staticmethod
    def sanitize_integer(value: str, min_val: int = None, max_val: int = None) -> int:
        """Sanitize and validate an integer."""
        try:
            num = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid integer: {value}")

        if min_val is not None and num < min_val:
            raise ValueError(f"Value {num} is below minimum {min_val}")

        if max_val is not None and num > max_val:
            raise ValueError(f"Value {num} exceeds maximum {max_val}")

        return num


def create_default_validator() -> SQLValidator:
    """Create a default SQL validator with common settings."""
    return SQLValidator(
        max_query_length=50000,
    )
