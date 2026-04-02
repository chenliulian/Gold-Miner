"""Tests for business_knowledge module."""

import unittest
import tempfile
import os
from pathlib import Path

from gold_miner.business_knowledge import BusinessKnowledgeManager, TableKnowledge, TableField


class TestBusinessKnowledgeManager(unittest.TestCase):
    """Test cases for BusinessKnowledgeManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.knowledge_dir = Path(self.temp_dir)
        self.tables_dir = self.knowledge_dir / "tables"
        self.tables_dir.mkdir(exist_ok=True)
        self.manager = BusinessKnowledgeManager(self.knowledge_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_yaml_file(self, filename, content):
        """Helper to create a YAML file."""
        filepath = self.tables_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_load_table_knowledge_with_dict_format(self):
        """Test loading table knowledge with dict format (original format)."""
        yaml_content = """
基本信息:
  表名: com_cdm.dim_ad_group_dd
  业务名称: 广告组维度表
  数据粒度: 广告组+日期
  更新频率: 每日
  保留周期: 90天

核心字段详解:
  ad_group_id:
    字段名: ad_group_id
    数据类型: BIGINT
    业务含义: 广告组ID
    示例值: [12345, 67890]
    使用注意: 唯一标识广告组
  ad_group_name:
    字段名: ad_group_name
    数据类型: STRING
    业务含义: 广告组名称
    示例值: ["测试广告组"]
    使用注意: 可能包含特殊字符

常用查询场景:
  查询广告组列表:
    场景名称: 查询指定账户下的广告组
    SQL模板: "SELECT * FROM com_cdm.dim_ad_group_dd WHERE account_id = {account_id}"
    参数:
      account_id: 账户ID

数据质量规则:
  异常值识别:
    无效广告组ID:
      条件: "ad_group_id IS NULL OR ad_group_id <= 0"
      可能原因: 数据同步异常
      建议: 检查上游数据源
"""
        self._create_yaml_file("com_cdm_dim_ad_group_dd.yaml", yaml_content)

        # Test loading
        result = self.manager._load_table_knowledge("com_cdm.dim_ad_group_dd")

        # Assertions
        self.assertIsNotNone(result)
        self.assertIsInstance(result, TableKnowledge)
        self.assertEqual(result.table_name, "com_cdm.dim_ad_group_dd")
        self.assertEqual(result.business_name, "广告组维度表")

        # Check core fields
        self.assertEqual(len(result.core_fields), 2)
        self.assertIn("ad_group_id", result.core_fields)
        self.assertIn("ad_group_name", result.core_fields)

        field = result.core_fields["ad_group_id"]
        self.assertIsInstance(field, TableField)
        self.assertEqual(field.name, "ad_group_id")
        self.assertEqual(field.data_type, "BIGINT")
        self.assertEqual(field.business_meaning, "广告组ID")

        # Check scenarios
        self.assertEqual(len(result.common_scenarios), 1)
        self.assertEqual(result.common_scenarios[0]["name"], "查询广告组列表")

        # Check quality rules
        self.assertEqual(len(result.quality_rules), 1)
        self.assertEqual(result.quality_rules[0]["name"], "无效广告组ID")

    def test_load_table_knowledge_with_list_format(self):
        """Test loading table knowledge with list format (new format)."""
        yaml_content = """
基本信息:
  表名: com_cdm.dim_ad_group_dd
  业务名称: 广告组维度表
  数据粒度: 广告组+日期
  更新频率: 每日
  保留周期: 90天

核心字段详解:
  - 字段名: ad_group_id
    数据类型: BIGINT
    业务含义: 广告组ID
    示例值: [12345, 67890]
    使用注意: 唯一标识广告组
  - 字段名: ad_group_name
    数据类型: STRING
    业务含义: 广告组名称
    示例值: ["测试广告组"]
    使用注意: 可能包含特殊字符
  - 字段名: transform_target_bill
    数据类型: BIGINT
    业务含义: 转化目标出价
    示例值: [3000, 5000]
    使用注意: 单位是千分之一美元

常用查询场景:
  - 场景名称: 查询指定账户下的广告组
    SQL模板: "SELECT * FROM com_cdm.dim_ad_group_dd WHERE account_id = {account_id}"
    参数:
      account_id: 账户ID
  - 场景名称: 查询广告组出价
    SQL模板: "SELECT ad_group_id, transform_target_bill FROM com_cdm.dim_ad_group_dd"
    参数: {}

数据质量规则:
  异常值识别:
    - 规则名: 无效广告组ID
      条件: "ad_group_id IS NULL OR ad_group_id <= 0"
      可能原因: 数据同步异常
      建议: 检查上游数据源
    - 规则名: 出价异常
      条件: "transform_target_bill < 0"
      可能原因: 数据错误
      建议: 联系数据团队
"""
        self._create_yaml_file("com_cdm_dim_ad_group_dd.yaml", yaml_content)

        # Test loading
        result = self.manager._load_table_knowledge("com_cdm.dim_ad_group_dd")

        # Assertions
        self.assertIsNotNone(result)
        self.assertIsInstance(result, TableKnowledge)
        self.assertEqual(result.table_name, "com_cdm.dim_ad_group_dd")
        self.assertEqual(result.business_name, "广告组维度表")

        # Check core fields
        self.assertEqual(len(result.core_fields), 3)
        self.assertIn("ad_group_id", result.core_fields)
        self.assertIn("ad_group_name", result.core_fields)
        self.assertIn("transform_target_bill", result.core_fields)

        field = result.core_fields["transform_target_bill"]
        self.assertIsInstance(field, TableField)
        self.assertEqual(field.name, "transform_target_bill")
        self.assertEqual(field.data_type, "BIGINT")
        self.assertEqual(field.business_meaning, "转化目标出价")

        # Check scenarios
        self.assertEqual(len(result.common_scenarios), 2)
        scenario_names = [s["name"] for s in result.common_scenarios]
        self.assertIn("查询指定账户下的广告组", scenario_names)
        self.assertIn("查询广告组出价", scenario_names)

        # Check quality rules
        self.assertEqual(len(result.quality_rules), 2)
        rule_names = [r["name"] for r in result.quality_rules]
        self.assertIn("无效广告组ID", rule_names)
        self.assertIn("出价异常", rule_names)

    def test_load_table_knowledge_with_mixed_format(self):
        """Test loading table knowledge with mixed format (dict for fields, list for scenarios)."""
        yaml_content = """
基本信息:
  表名: com_cdm.dim_ad_group_dd
  业务名称: 广告组维度表

核心字段详解:
  ad_group_id:
    字段名: ad_group_id
    数据类型: BIGINT
    业务含义: 广告组ID

常用查询场景:
  - 场景名称: 查询广告组
    SQL模板: "SELECT * FROM table"
    参数: {}

数据质量规则:
  异常值识别:
    - 规则名: 无效ID
      条件: "id IS NULL"
      可能原因: 数据错误
      建议: 检查数据
"""
        self._create_yaml_file("com_cdm_dim_ad_group_dd.yaml", yaml_content)

        # Test loading - should not raise exception
        result = self.manager._load_table_knowledge("com_cdm.dim_ad_group_dd")

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(len(result.core_fields), 1)
        self.assertEqual(len(result.common_scenarios), 1)
        self.assertEqual(len(result.quality_rules), 1)

    def test_load_table_knowledge_empty_fields(self):
        """Test loading table knowledge with empty or missing fields."""
        yaml_content = """
基本信息:
  表名: com_cdm.test_table
  业务名称: 测试表
"""
        self._create_yaml_file("com_cdm_test_table.yaml", yaml_content)

        # Test loading
        result = self.manager._load_table_knowledge("com_cdm.test_table")

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(len(result.core_fields), 0)
        self.assertEqual(len(result.common_scenarios), 0)
        self.assertEqual(len(result.quality_rules), 0)

    def test_find_matching_tables_with_dict_format(self):
        """Test find_matching_tables with dict format."""
        yaml_content = """
基本信息:
  表名: com_cdm.dim_ad_group_dd
  业务名称: 广告组维度表

核心字段详解:
  ad_group_id:
    字段名: ad_group_id
    数据类型: BIGINT
    业务含义: 广告组ID，用于唯一标识广告组
"""
        self._create_yaml_file("com_cdm_dim_ad_group_dd.yaml", yaml_content)

        # Test matching - use table name keyword to match
        matches = self.manager.find_matching_tables("查询 dim_ad_group 表")

        # Should find the table
        self.assertGreater(len(matches), 0)
        self.assertEqual(matches[0]["table_name"], "com_cdm.dim_ad_group_dd")

    def test_find_matching_tables_with_list_format(self):
        """Test find_matching_tables with list format."""
        yaml_content = """
基本信息:
  表名: com_cdm.dim_ad_group_dd
  业务名称: 广告组维度表

核心字段详解:
  - 字段名: ad_group_id
    数据类型: BIGINT
    业务含义: 广告组ID，用于唯一标识广告组
  - 字段名: transform_target_bill
    数据类型: BIGINT
    业务含义: 转化目标出价，单位是千分之一美元
"""
        self._create_yaml_file("com_cdm_dim_ad_group_dd.yaml", yaml_content)

        # Test matching with field name
        matches = self.manager.find_matching_tables("查询transform_target_bill字段")

        # Should find the table
        self.assertGreater(len(matches), 0)
        self.assertEqual(matches[0]["table_name"], "com_cdm.dim_ad_group_dd")

        # Test matching with business meaning - use longer keyword (>2 chars)
        matches = self.manager.find_matching_tables("查询dim_ad_group表数据")

        # Should find the table
        self.assertGreater(len(matches), 0)

    def test_load_nonexistent_table(self):
        """Test loading a table that doesn't exist."""
        result = self.manager._load_table_knowledge("nonexistent.table")
        self.assertIsNone(result)

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML content."""
        yaml_content = "invalid: yaml: content: ["
        self._create_yaml_file("invalid_table.yaml", yaml_content)

        # Should not raise exception, return None
        result = self.manager._load_table_knowledge("invalid.table")
        self.assertIsNone(result)


class TestTableKnowledge(unittest.TestCase):
    """Test cases for TableKnowledge dataclass."""

    def test_table_knowledge_creation(self):
        """Test creating TableKnowledge object."""
        tk = TableKnowledge(
            table_name="test.table",
            business_name="测试表",
            data_granularity="天",
            update_frequency="每日",
            retention_period="90天",
            core_fields={},
            common_scenarios=[],
            quality_rules=[]
        )

        self.assertEqual(tk.table_name, "test.table")
        self.assertEqual(tk.business_name, "测试表")


class TestTableField(unittest.TestCase):
    """Test cases for TableField dataclass."""

    def test_table_field_creation(self):
        """Test creating TableField object."""
        field = TableField(
            name="test_field",
            data_type="STRING",
            business_meaning="测试字段",
            examples=["value1", "value2"],
            notes="注意事项"
        )

        self.assertEqual(field.name, "test_field")
        self.assertEqual(field.data_type, "STRING")
        self.assertEqual(field.business_meaning, "测试字段")
        self.assertEqual(len(field.examples), 2)


if __name__ == "__main__":
    unittest.main()
