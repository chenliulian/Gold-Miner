"""业务知识管理系统

负责管理和检索业务知识，包括：
- 业务术语 (Glossary)
- 表结构知识 (Table Schema)
- 查询规则 (Query Rules)
- 查询模式 (Query Patterns)
"""
from __future__ import annotations

import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class BusinessTerm:
    """业务术语定义"""
    name: str
    english: str
    definition: str
    formula: str = ""
    related_fields: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class TableField:
    """表字段信息"""
    name: str
    data_type: str
    business_meaning: str
    examples: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class TableKnowledge:
    """表知识"""
    table_name: str
    business_name: str
    data_granularity: str
    update_frequency: str
    retention_period: str
    core_fields: Dict[str, TableField] = field(default_factory=dict)
    common_scenarios: List[Dict] = field(default_factory=list)
    quality_rules: List[Dict] = field(default_factory=list)


@dataclass
class QueryRule:
    """查询规则"""
    rule_id: str
    name: str
    description: str
    severity: str  # 强制/警告/建议
    applicable_tables: List[str]
    correct_example: str
    incorrect_example: str


@dataclass
class QueryContext:
    """查询上下文"""
    terms: List[BusinessTerm] = field(default_factory=list)
    tables: List[TableKnowledge] = field(default_factory=list)
    rules: List[QueryRule] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class BusinessKnowledgeManager:
    """业务知识管理器
    
    统一管理业务知识的加载、检索和应用
    """
    
    def __init__(self, knowledge_dir: str = None):
        """初始化知识管理器
        
        Args:
            knowledge_dir: 知识库目录路径，默认为项目根目录下的 knowledge
        """
        if knowledge_dir is None:
            # 默认路径：项目根目录/knowledge
            # 从当前文件位置向上回溯到项目根目录
            # src/gold_miner/business_knowledge.py -> 回溯3层到项目根目录
            project_root = Path(__file__).resolve().parent.parent.parent
            knowledge_dir = project_root / "knowledge"
        
        self.knowledge_dir = Path(knowledge_dir).resolve()
        self.glossary_dir = self.knowledge_dir / "glossary"
        self.tables_dir = self.knowledge_dir / "tables"
        self.rules_dir = self.knowledge_dir / "rules"
        
        # 缓存
        self._glossary_cache: Dict[str, BusinessTerm] = {}
        self._table_cache: Dict[str, TableKnowledge] = {}
        self._rules_cache: List[QueryRule] = []
        
        # 加载知识
        self._load_all_knowledge()
    
    def _load_all_knowledge(self):
        """加载所有知识文件"""
        self._load_glossary()
        self._load_rules()
        # 表知识按需加载
    
    def _load_glossary(self):
        """加载业务术语"""
        if not self.glossary_dir.exists():
            return
        
        for file_path in self.glossary_dir.glob("*.yaml"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if data and '术语定义' in data:
                    for term_name, term_data in data['术语定义'].items():
                        term = BusinessTerm(
                            name=term_name,
                            english=term_data.get('英文', ''),
                            definition=term_data.get('定义', ''),
                            formula=term_data.get('计算公式', ''),
                            related_fields=term_data.get('相关字段', []),
                            examples=term_data.get('示例值', [])
                        )
                        self._glossary_cache[term_name] = term
                        # 也按英文名称索引
                        if term.english:
                            for eng_name in term.english.split('/'):
                                self._glossary_cache[eng_name.strip()] = term
            except Exception as e:
                print(f"[Knowledge] 加载术语文件失败 {file_path}: {e}")
    
    def _load_rules(self):
        """加载查询规则"""
        rules_file = self.rules_dir / "query_rules.yaml"
        if not rules_file.exists():
            return
        
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data and '查询规则' in data:
                for rule_name, rule_data in data['查询规则'].items():
                    rule = QueryRule(
                        rule_id=rule_data.get('规则ID', ''),
                        name=rule_name,
                        description=rule_data.get('描述', ''),
                        severity=rule_data.get('严重级别', '建议'),
                        applicable_tables=rule_data.get('适用表', []),
                        correct_example=rule_data.get('正确示例', ''),
                        incorrect_example=rule_data.get('错误示例', '')
                    )
                    self._rules_cache.append(rule)
        except Exception as e:
            print(f"[Knowledge] 加载规则文件失败: {e}")
    
    def find_matching_tables(self, question: str) -> List[Dict]:
        """根据用户问题查找匹配的表
        
        从 knowledge/tables 目录下的 YAML 文件中匹配
        
        Args:
            question: 用户问题
            
        Returns:
            匹配的表信息列表，按相关度排序
        """
        matches = []
        question_lower = question.lower()
        
        # 遍历 knowledge/tables 目录下的所有 YAML 文件
        if not self.tables_dir.exists():
            return matches
        
        for yaml_file in self.tables_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if not data or '基本信息' not in data:
                    continue
                
                basic_info = data['基本信息']
                table_name = basic_info.get('表名', '')
                business_name = basic_info.get('业务名称', '')
                
                if not table_name:
                    continue
                
                score = 0
                table_name_lower = table_name.lower()
                
                # 1. 检查表名是否直接出现在问题中
                if table_name_lower in question_lower:
                    score += 100
                
                # 2. 检查业务名称是否出现在问题中
                if business_name and business_name.lower() in question_lower:
                    score += 80
                
                # 3. 检查别名是否出现在问题中
                aliases = basic_info.get('别名', [])
                for alias in aliases:
                    if alias.lower() in question_lower:
                        score += 90
                
                # 4. 检查表名中的关键词匹配
                table_keywords = table_name.replace('.', '_').split('_')
                for keyword in table_keywords:
                    if len(keyword) > 2 and keyword.lower() in question_lower:
                        score += 20
                
                # 5. 检查核心字段名是否出现在问题中
                if '核心字段详解' in data:
                    core_fields_data = data['核心字段详解']
                    if isinstance(core_fields_data, dict):
                        for field_name, field_data in core_fields_data.items():
                            if field_name.lower() in question_lower:
                                score += 10
                            # 检查字段业务含义
                            business_meaning = field_data.get('业务含义', '')
                            if business_meaning and business_meaning.lower() in question_lower:
                                score += 15
                    elif isinstance(core_fields_data, list):
                        for field_data in core_fields_data:
                            if isinstance(field_data, dict):
                                field_name = field_data.get('字段名', '')
                                if field_name and field_name.lower() in question_lower:
                                    score += 10
                                # 检查字段业务含义
                                business_meaning = field_data.get('业务含义', '')
                                if business_meaning and business_meaning.lower() in question_lower:
                                    score += 15
                
                if score > 0:
                    matches.append({
                        'table_name': table_name,
                        'score': score,
                        'business_name': business_name
                    })
            except Exception as e:
                print(f"[Knowledge] 匹配表失败 {yaml_file}: {e}")
        
        # 按分数排序
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches
    
    def _load_table_knowledge(self, table_name: str) -> Optional[TableKnowledge]:
        """加载表知识
        
        从 knowledge/tables 加载
        """
        # 清理表名
        clean_name = table_name.replace('.', '_').replace('-', '_')
        
        # 检查缓存
        if table_name in self._table_cache:
            return self._table_cache[table_name]
        
        # 从 knowledge/tables 加载
        knowledge_file = self.tables_dir / f"{clean_name}.yaml"
        if knowledge_file.exists():
            return self._load_from_knowledge_file(table_name, knowledge_file)
        
        return None
    
    def _load_from_knowledge_file(self, table_name: str, knowledge_file: Path) -> Optional[TableKnowledge]:
        """从 knowledge/tables YAML 文件加载表知识"""
        
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return None
            
            # 解析核心字段
            core_fields = {}
            if '核心字段详解' in data:
                core_fields_data = data['核心字段详解']
                # 支持字典或列表格式
                if isinstance(core_fields_data, dict):
                    for field_name, field_data in core_fields_data.items():
                        field = TableField(
                            name=field_data.get('字段名', field_name),
                            data_type=field_data.get('数据类型', 'UNKNOWN'),
                            business_meaning=field_data.get('业务含义', ''),
                            examples=field_data.get('示例值', []),
                            notes=field_data.get('使用注意', '')
                        )
                        core_fields[field_name] = field
                elif isinstance(core_fields_data, list):
                    for field_data in core_fields_data:
                        if isinstance(field_data, dict):
                            field_name = field_data.get('字段名', '')
                            if field_name:
                                field = TableField(
                                    name=field_name,
                                    data_type=field_data.get('数据类型', 'UNKNOWN'),
                                    business_meaning=field_data.get('业务含义', ''),
                                    examples=field_data.get('示例值', []),
                                    notes=field_data.get('使用注意', '')
                                )
                                core_fields[field_name] = field
            
            # 解析常用场景
            common_scenarios = []
            if '常用查询场景' in data:
                scenarios_data = data['常用查询场景']
                if isinstance(scenarios_data, dict):
                    for scenario_name, scenario_data in scenarios_data.items():
                        common_scenarios.append({
                            'name': scenario_name,
                            'description': scenario_data.get('场景名称', ''),
                            'sql_template': scenario_data.get('SQL模板', ''),
                            'params': scenario_data.get('参数', {})
                        })
                elif isinstance(scenarios_data, list):
                    for scenario_data in scenarios_data:
                        if isinstance(scenario_data, dict):
                            common_scenarios.append({
                                'name': scenario_data.get('场景名称', ''),
                                'description': scenario_data.get('场景名称', ''),
                                'sql_template': scenario_data.get('SQL模板', ''),
                                'params': scenario_data.get('参数', {})
                            })
            
            # 解析质量规则
            quality_rules = []
            if '数据质量规则' in data and '异常值识别' in data['数据质量规则']:
                rules_data = data['数据质量规则']['异常值识别']
                if isinstance(rules_data, dict):
                    for rule_name, rule_data in rules_data.items():
                        quality_rules.append({
                            'name': rule_name,
                            'condition': rule_data.get('条件', ''),
                            'reason': rule_data.get('可能原因', ''),
                            'suggestion': rule_data.get('建议', '')
                        })
                elif isinstance(rules_data, list):
                    for rule_data in rules_data:
                        if isinstance(rule_data, dict):
                            quality_rules.append({
                                'name': rule_data.get('规则名', ''),
                                'condition': rule_data.get('条件', ''),
                                'reason': rule_data.get('可能原因', ''),
                                'suggestion': rule_data.get('建议', '')
                            })
            
            # 创建表知识对象
            basic_info = data.get('基本信息', {})
            table_knowledge = TableKnowledge(
                table_name=basic_info.get('表名', table_name),
                business_name=basic_info.get('业务名称', ''),
                data_granularity=basic_info.get('数据粒度', ''),
                update_frequency=basic_info.get('更新频率', ''),
                retention_period=basic_info.get('保留周期', ''),
                core_fields=core_fields,
                common_scenarios=common_scenarios,
                quality_rules=quality_rules
            )
            
            # 缓存
            self._table_cache[table_name] = table_knowledge
            return table_knowledge
            
        except Exception as e:
            print(f"[Knowledge] 加载表知识失败 {table_name}: {e}")
            return None
    
    def extract_terms(self, text: str) -> List[BusinessTerm]:
        """从文本中提取业务术语
        
        Args:
            text: 用户输入的文本
            
        Returns:
            识别到的业务术语列表
        """
        found_terms = []
        text_lower = text.lower()
        
        for term_name, term in self._glossary_cache.items():
            # 检查术语是否出现在文本中
            if term_name.lower() in text_lower:
                # 避免重复添加
                if term not in found_terms:
                    found_terms.append(term)
        
        return found_terms
    
    def identify_tables(self, text: str) -> List[str]:
        """从文本中识别可能涉及的表
        
        从 knowledge/tables 目录下的 YAML 文件中匹配
        
        Args:
            text: 用户输入的文本
            
        Returns:
            表名列表
        """
        tables = []
        text_lower = text.lower()
        
        # 1. 从 knowledge/tables 目录匹配表名
        if self.tables_dir.exists():
            for yaml_file in self.tables_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    
                    if data and '基本信息' in data:
                        table_name = data['基本信息'].get('表名', '')
                        if table_name and table_name.lower() in text_lower:
                            tables.append(table_name)
                except Exception as e:
                    print(f"[Knowledge] 识别表失败 {yaml_file}: {e}")
        
        # 2. 模式匹配：识别表名模式（作为备选）
        if not tables:
            patterns = [
                r'mi_ads_dmp\.\w+',  # 完整表名
                r'com_cdm\.\w+',     # com_cdm 表
                r'dwd_\w+',  # DWD表
                r'dws_\w+',  # DWS表
                r'ads_\w+',  # ADS表
                r'dim_\w+',  # 维度表
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                tables.extend(matches)
        
        return list(set(tables))
    
    def get_relevant_rules(self, tables: List[str]) -> List[QueryRule]:
        """获取相关的查询规则
        
        Args:
            tables: 涉及的表名列表
            
        Returns:
            适用的查询规则列表
        """
        relevant_rules = []
        
        for rule in self._rules_cache:
            # 检查规则是否适用于这些表
            if not rule.applicable_tables:
                # 通用规则
                relevant_rules.append(rule)
            else:
                for table in tables:
                    for pattern in rule.applicable_tables:
                        if pattern == '*' or pattern in table:
                            relevant_rules.append(rule)
                            break
        
        return relevant_rules
    
    def build_context(self, question: str) -> QueryContext:
        """构建查询上下文
        
        Args:
            question: 用户问题
            
        Returns:
            包含业务知识的查询上下文
        """
        context = QueryContext()
        
        # 1. 提取业务术语
        context.terms = self.extract_terms(question)
        
        # 2. 识别涉及的表（从 knowledge/tables 中匹配）
        table_names = self.identify_tables(question)
        
        # 3. 如果没有识别到表，尝试从 knowledge/tables 中模糊匹配
        if not table_names:
            matched_tables = self.find_matching_tables(question)
            if matched_tables:
                # 使用匹配度最高的表
                best_match = matched_tables[0]
                table_names = [best_match['table_name']]
                context.notes.append(f"🎯 根据您的问题，自动推荐表: {best_match['table_name']}")
        
        # 4. 加载表知识
        for table_name in table_names:
            table_knowledge = self._load_table_knowledge(table_name)
            if table_knowledge:
                context.tables.append(table_knowledge)
        
        # 5. 获取相关规则
        context.rules = self.get_relevant_rules(table_names)
        
        # 6. 生成注意事项
        context.notes.extend(self._generate_notes(context))
        
        return context
    
    def _generate_notes(self, context: QueryContext) -> List[str]:
        """生成注意事项"""
        notes = []
        
        # 检查是否需要分区条件
        for table in context.tables:
            if 'dwd' in table.table_name.lower():
                notes.append(f"⚠️ 表 {table.table_name} 是DWD明细表，查询时必须指定 dh 分区条件")
        
        # 检查消耗计算
        for term in context.terms:
            if '消耗' in term.name:
                notes.append(f"💡 消耗计算口径: {term.formula}")
        
        return notes
    
    def format_context_for_prompt(self, context: QueryContext) -> str:
        """将上下文格式化为 Prompt 可用的字符串
        
        Args:
            context: 查询上下文
            
        Returns:
            格式化后的字符串
        """
        sections = []
        
        # 1. 业务术语
        if context.terms:
            sections.append("## 业务术语")
            for term in context.terms:
                sections.append(f"- **{term.name}** ({term.english}): {term.definition}")
                if term.formula:
                    sections.append(f"  - 计算公式: {term.formula}")
            sections.append("")
        
        # 2. 表信息
        if context.tables:
            sections.append("## 表结构信息")
            for table in context.tables:
                sections.append(f"### {table.table_name}")
                sections.append(f"业务名称: {table.business_name}")
                sections.append(f"数据粒度: {table.data_granularity}")
                sections.append(f"更新频率: {table.update_frequency}")
                
                # 展示所有核心字段（带使用注意）
                if table.core_fields:
                    sections.append("核心字段详解:")
                    for field_name, field in table.core_fields.items():
                        field_desc = f"  - **{field.name}** ({field.data_type}): {field.business_meaning}"
                        if field.notes:
                            field_desc += f" [注意: {field.notes}]"
                        sections.append(field_desc)
                
                # 展示常用查询场景
                if table.common_scenarios:
                    sections.append("常用查询场景:")
                    for scenario in table.common_scenarios:
                        sections.append(f"  - {scenario['name']}: {scenario['description']}")
                        if scenario['sql_template']:
                            sections.append(f"    SQL模板: {scenario['sql_template'][:200]}...")
                
                # 展示数据质量规则
                if table.quality_rules:
                    sections.append("数据质量规则:")
                    for rule in table.quality_rules:
                        sections.append(f"  - {rule['name']}: {rule['condition']}")
                        if rule['suggestion']:
                            sections.append(f"    建议: {rule['suggestion']}")
                
                sections.append("")
        
        # 3. 查询规则
        if context.rules:
            sections.append("## 查询规则")
            for rule in context.rules:
                # 所有级别的规则都加载：强制、警告、建议
                sections.append(f"- **{rule.name}** ({rule.severity}): {rule.description}")
                if rule.correct_example:
                    sections.append(f"  - 正确示例: {rule.correct_example[:100]}...")
                if rule.incorrect_example:
                    sections.append(f"  - 错误示例: {rule.incorrect_example[:100]}...")
            sections.append("")
        
        # 4. 注意事项
        if context.notes:
            sections.append("## 注意事项")
            for note in context.notes:
                sections.append(f"{note}")
            sections.append("")
        
        return "\n".join(sections)


# 全局知识管理器实例
_knowledge_manager: Optional[BusinessKnowledgeManager] = None


def get_knowledge_manager() -> BusinessKnowledgeManager:
    """获取全局知识管理器实例（单例模式）"""
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = BusinessKnowledgeManager()
    return _knowledge_manager
