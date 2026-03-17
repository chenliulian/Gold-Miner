# SQL 分析 Agent 业务知识管理系统设计

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    业务知识管理系统                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  业务术语层   │  │  表结构知识层 │  │  业务规则层   │          │
│  │  (Glossary)  │  │  (Schema)    │  │  (Rules)     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                     │
│              ┌────────────────────────┐                        │
│              │     知识融合引擎        │                        │
│              │  (Knowledge Fusion)    │                        │
│              └───────────┬────────────┘                        │
│                          ▼                                      │
│              ┌────────────────────────┐                        │
│              │   SQL 生成与优化器      │                        │
│              │  (SQL Generator)       │                        │
│              └────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 核心模块设计

### 2.1 业务术语层 (Business Glossary)

**目的**: 建立统一的业务语言，让 Agent 理解广告业务概念

```yaml
# business_glossary.yaml
术语定义:
  消耗:
    英文: spend / cost
    定义: 广告投放实际扣费金额，单位通常为微美元
    计算公式: billing_actual_deduction_price / 1e5 (转为美元)
    相关字段: [billing_actual_deduction_price, cost_micro_usd]
    常用口径:
      - 总消耗: SUM(billing_actual_deduction_price) / 1e5
      - 日均消耗: AVG(daily_spend)
    
  展示:
    英文: impression / show
    定义: 广告被展示给用户的次数
    相关字段: [show_count, impression_cnt, imp]
    
  点击:
    英文: click
    定义: 用户点击广告的次数
    相关字段: [click_count, clk, click_cnt]
    
  CTR:
    英文: Click Through Rate
    定义: 点击率 = 点击数 / 展示数
    计算公式: click_count / show_count
    常见阈值: 
      - 优秀: > 2%
      - 一般: 1% - 2%
      - 较差: < 1%
    
  CVR:
    英文: Conversion Rate
    定义: 转化率 = 转化数 / 点击数
    计算公式: conversion_count / click_count
    
  广告主:
    英文: advertiser
    定义: 投放广告的客户
    相关字段: [advertiser_id, adv_id, customer_id]
    
  广告组:
    英文: adgroup
    定义: 广告计划下的投放单元
    相关字段: [adgroup_id, adg_id, unit_id]
    
  广告计划:
    英文: campaign
    定义: 广告主的投放计划
    相关字段: [campaign_id, cmp_id, plan_id]

分层概念:
  DWD层:
    全称: Data Warehouse Detail
    定义: 明细数据层，存储最细粒度的数据
    特点: 
      - 数据粒度最细
      - 包含完整的历史数据
      - 通常按小时/天分区
    
  DWS层:
    全称: Data Warehouse Service
    定义: 服务数据层，轻度汇总
    特点:
      - 按业务主题汇总
      - 适合分析查询
      
  ADS层:
    全称: Application Data Service
    定义: 应用数据层，高度汇总
    特点:
      - 直接面向业务应用
      - 查询性能最优
```

### 2.2 表结构知识层 (Schema Knowledge)

**目的**: 让 Agent 理解每个表的业务含义和使用场景

```yaml
# table_knowledge.yaml
表知识库:
  mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi:
    业务名称: 广告展示点击转化明细表
    数据粒度: 单次广告曝光级别
    更新频率: 小时级
    保留周期: 90天
    
    核心字段解读:
      dh:
        含义: 数据小时分区
        格式: YYYYMMDDHH
        示例: "2026031500" 表示 2026年3月15日0点
        使用注意: 查询时必须指定dh范围，否则数据量过大
        
      billing_actual_deduction_price:
        含义: 实际扣费金额（微美元）
        业务意义: 真实的广告消耗
        单位转换: /1e5 转为美元
        常用计算:
          - 总消耗: SUM(billing_actual_deduction_price) / 1e5
          - 平均CPM: SUM(billing_actual_deduction_price) / SUM(show_count) * 1000
          
      cost_type:
        含义: 扣费类型
        枚举值:
          - "CPC": 按点击付费
          - "CPM": 按展示付费
          - "oCPC": 优化点击付费
          - "oCPM": 优化展示付费
        
      advertiser_id:
        含义: 广告主ID
        关联表: dim_advertiser
        使用场景: 按广告主分析消耗
        
    常用查询场景:
      场景1_查询某小时总消耗:
        SQL模板: |
          SELECT 
            '{biz_date}' AS biz_date,
            SUM(billing_actual_deduction_price) / 1e5 AS spend_usd
          FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
          WHERE dh >= '{biz_date}00' AND dh <= '{biz_date}23';
        参数:
          biz_date: 业务日期，格式YYYYMMDD
          
      场景2_查询广告主消耗TOP10:
        SQL模板: |
          SELECT 
            advertiser_id,
            SUM(billing_actual_deduction_price) / 1e5 AS spend_usd,
            SUM(show_count) AS impressions,
            SUM(click_count) AS clicks,
            ROUND(SUM(click_count) / SUM(show_count), 4) AS ctr
          FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
          WHERE dh >= '{start_date}00' AND dh <= '{end_date}23'
          GROUP BY advertiser_id
          ORDER BY spend_usd DESC
          LIMIT 10;
          
      场景3_分小时消耗趋势:
        SQL模板: |
          SELECT 
            dh,
            SUM(billing_actual_deduction_price) / 1e5 AS spend_usd
          FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
          WHERE dh >= '{start_hour}' AND dh <= '{end_hour}'
          GROUP BY dh
          ORDER BY dh;
```

### 2.3 业务规则层 (Business Rules)

**目的**: 定义业务约束和最佳实践

```yaml
# business_rules.yaml
业务规则:
  数据查询规则:
    必须指定分区:
      描述: 查询DWD层表必须指定分区条件
      原因: 避免全表扫描，提高查询性能
      适用表: [dwd_ew_ads_show_res_clk_dld_conv_hi, dwd_ew_ads_*]
      示例: WHERE dh >= '2026031500' AND dh <= '2026031523'
      
    时间范围限制:
      描述: 单次查询时间范围不超过31天
      原因: 防止查询超时，保护系统资源
      建议: 大范围查询分多次执行
      
    聚合查询优化:
      描述: 大表聚合前先过滤
      原因: 减少计算量
      反例: SELECT ... FROM table GROUP BY ... HAVING ...
      正例: SELECT ... FROM (SELECT ... FROM table WHERE ...) GROUP BY ...

  指标计算规则:
    消耗统一口径:
      描述: 所有消耗类指标使用 billing_actual_deduction_price / 1e5
      原因: 统一单位，避免混淆
      注意: 不要用其他 price 字段
      
    CTR计算:
      描述: CTR = SUM(click_count) / SUM(show_count)
      注意: 是先SUM再除，不是先除再SUM
      反例: AVG(click_count / show_count)
      正例: SUM(click_count) / SUM(show_count)
      
    去重规则:
      描述: 按用户去重使用 request_id，按广告去重使用 adgroup_id
      原因: request_id 是每次请求唯一，adgroup_id 是广告单元唯一

  数据质量规则:
    异常值识别:
      CTR异常:
        - CTR > 10%: 可能数据异常或作弊流量
        - CTR < 0.1%: 可能投放效果差或定向过宽
      CVR异常:
        - CVR > 50%: 可能数据异常
        - CVR < 0.01%: 转化链路可能有问题
        
    数据完整性检查:
      检查项:
        - 消耗为0但有展示: 可能是赠送流量或数据缺失
        - 展示为0但有消耗: 数据异常
        - 点击 > 展示: 数据逻辑错误
```

## 3. 渐进式学习机制

### 3.1 学习阶段设计

```
阶段1: 基础认知 (初次接触)
├── 了解表的基本结构
├── 识别核心字段
├── 理解数据粒度
└── 掌握基本查询方式

阶段2: 业务理解 (深入探索)
├── 理解字段业务含义
├── 掌握常用计算口径
├── 了解数据更新规律
└── 熟悉典型查询场景

阶段3: 规则掌握 (熟练应用)
├── 遵循查询优化规则
├── 识别数据异常
├── 选择最佳查询路径
└── 复用已有查询模式

阶段4: 创新应用 (专家级)
├── 组合多个表分析
├── 发现新的分析角度
├── 优化查询性能
└── 沉淀新的业务知识
```

### 3.2 知识积累流程

```
用户提问
    │
    ▼
┌─────────────────┐
│ 1. 意图识别     │ ← 匹配业务术语
│   (Intent)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 知识检索     │ ← 查询表结构知识
│   (Retrieve)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. SQL生成      │ ← 应用业务规则
│   (Generate)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. 结果验证     │ ← 检查数据质量
│   (Validate)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. 知识沉淀     │ ← 保存新的理解
│   (Learn)       │
└─────────────────┘
```

## 4. 技术实现方案

### 4.1 知识存储结构

```
project/
├── knowledge/                    # 业务知识目录
│   ├── glossary/                # 术语定义
│   │   ├── core_terms.yaml      # 核心术语
│   │   ├── metrics.yaml         # 指标定义
│   │   └── dimensions.yaml      # 维度定义
│   │
│   ├── tables/                  # 表知识
│   │   ├── dwd_ew_ads_show_res_clk_dld_conv_hi.yaml
│   │   ├── dim_advertiser.yaml
│   │   └── ...
│   │
│   ├── rules/                   # 业务规则
│   │   ├── query_rules.yaml     # 查询规则
│   │   ├── metric_rules.yaml    # 指标规则
│   │   └── quality_rules.yaml   # 质量规则
│   │
│   ├── patterns/                # 查询模式
│   │   ├── spend_analysis.yaml  # 消耗分析模式
│   │   ├── performance_analysis.yaml
│   │   └── ...
│   │
│   └── experience/              # 经验积累
│       ├── successful_queries.yaml
│       ├── failed_cases.yaml
│       └── optimization_tips.yaml
│
└── memory/                      # 对话记忆
    └── conversations/
```

### 4.2 核心组件实现

```python
# business_knowledge_manager.py
class BusinessKnowledgeManager:
    """业务知识管理器 - 统一管理业务知识"""
    
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.glossary = GlossaryManager(self.knowledge_dir / "glossary")
        self.table_knowledge = TableKnowledgeManager(self.knowledge_dir / "tables")
        self.rule_engine = RuleEngine(self.knowledge_dir / "rules")
        self.pattern_library = PatternLibrary(self.knowledge_dir / "patterns")
    
    def understand_query(self, question: str) -> QueryIntent:
        """
        理解用户查询意图
        
        1. 识别业务术语
        2. 匹配查询模式
        3. 确定分析目标
        """
        # 提取术语
        terms = self.glossary.extract_terms(question)
        
        # 匹配意图
        intent = self._match_intent(question, terms)
        
        return QueryIntent(
            terms=terms,
            intent_type=intent.type,
            target_tables=intent.tables,
            metrics=intent.metrics,
            dimensions=intent.dimensions,
        )
    
    def generate_sql_context(self, intent: QueryIntent) -> SQLContext:
        """
        生成 SQL 上下文
        
        包含：
        - 表结构信息
        - 字段业务含义
        - 推荐查询模式
        - 注意事项
        """
        context = SQLContext()
        
        for table in intent.target_tables:
            # 获取表知识
            table_info = self.table_knowledge.get(table)
            context.add_table_info(table_info)
            
            # 获取常用查询模式
            patterns = self.pattern_library.get_patterns(table, intent.intent_type)
            context.add_patterns(patterns)
        
        # 应用业务规则
        rules = self.rule_engine.get_applicable_rules(intent)
        context.add_rules(rules)
        
        return context
    
    def learn_from_execution(self, question: str, sql: str, result: dict):
        """
        从执行结果中学习
        
        1. 记录成功的查询模式
        2. 分析数据特征
        3. 更新业务理解
        """
        # 保存查询模式
        self.pattern_library.add_pattern(question, sql, result)
        
        # 分析数据质量
        quality_issues = self._analyze_data_quality(result)
        if quality_issues:
            self.rule_engine.add_quality_rule(quality_issues)


# table_knowledge_manager.py
class TableKnowledgeManager:
    """表知识管理器"""
    
    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = knowledge_dir
        self._cache = {}
    
    def get(self, table_name: str) -> TableKnowledge:
        """获取表知识（带缓存）"""
        if table_name not in self._cache:
            knowledge_file = self.knowledge_dir / f"{table_name}.yaml"
            if knowledge_file.exists():
                self._cache[table_name] = self._load(knowledge_file)
            else:
                # 如果知识文件不存在，触发探索
                self._cache[table_name] = self._explore_table(table_name)
        
        return self._cache[table_name]
    
    def _explore_table(self, table_name: str) -> TableKnowledge:
        """探索新表并生成知识"""
        # 调用 explore_table skill
        result = explore_table.run(table_name)
        
        # 生成知识文件
        knowledge = self._generate_knowledge(result)
        self._save_knowledge(table_name, knowledge)
        
        return knowledge
    
    def update_field_meaning(self, table: str, field: str, meaning: str):
        """更新字段业务含义（用户反馈）"""
        knowledge = self.get(table)
        knowledge.fields[field].business_meaning = meaning
        self._save_knowledge(table, knowledge)
```

### 4.3 Prompt 增强设计

```python
# enhanced_prompts.py

BUSINESS_CONTEXT_TEMPLATE = """
# 业务背景知识

## 用户问题
{question}

## 识别到的业务术语
{terms}

## 相关表信息
{table_info}

## 推荐查询模式
{patterns}

## 业务规则提醒
{rules}

## 注意事项
{notes}

请基于以上业务知识生成 SQL 查询。
"""

def build_business_context(
    question: str,
    knowledge_manager: BusinessKnowledgeManager
) -> str:
    """构建包含业务知识的上下文"""
    
    # 理解意图
    intent = knowledge_manager.understand_query(question)
    
    # 生成上下文
    context = knowledge_manager.generate_sql_context(intent)
    
    # 格式化术语
    terms_str = "\n".join([
        f"- {term.name}: {term.definition}"
        for term in intent.terms
    ])
    
    # 格式化表信息
    table_info_str = "\n\n".join([
        f"### {table.name}\n"
        f"业务含义: {table.business_name}\n"
        f"核心字段:\n" +
        "\n".join([f"  - {f.name}: {f.business_meaning}" 
                   for f in table.core_fields])
        for table in context.tables
    ])
    
    # 格式化规则
    rules_str = "\n".join([
        f"- {rule.name}: {rule.description}"
        for rule in context.rules
    ])
    
    return BUSINESS_CONTEXT_TEMPLATE.format(
        question=question,
        terms=terms_str,
        table_info=table_info_str,
        patterns=context.patterns,
        rules=rules_str,
        notes=context.notes,
    )
```

## 5. 实施路线图

### Phase 1: 基础搭建 (1-2周)
- [ ] 创建业务术语库（核心术语）
- [ ] 实现表探索增强（自动生成知识文件）
- [ ] 设计知识存储结构

### Phase 2: 知识填充 (2-3周)
- [ ] 填充主要业务表的知识
- [ ] 定义常用查询模式
- [ ] 建立业务规则库

### Phase 3: 集成优化 (1-2周)
- [ ] 集成到 Agent Prompt
- [ ] 实现知识检索机制
- [ ] 添加用户反馈收集

### Phase 4: 持续学习 (长期)
- [ ] 分析成功/失败案例
- [ ] 自动发现新的查询模式
- [ ] 优化知识推荐算法

## 6. 预期效果

### 对 Agent 的提升
1. **理解更准确**: 理解"消耗"应该使用 `billing_actual_deduction_price / 1e5`
2. **查询更规范**: 自动添加分区条件，避免全表扫描
3. **结果更可靠**: 识别数据异常，给出质量提醒
4. **学习更快速**: 复用已有模式，减少重复探索

### 对用户的价值
1. **提问更自然**: 直接用业务语言提问，无需关心技术细节
2. **结果更可解释**: Agent 能说明为什么这样查询
3. **分析更专业**: 自动应用最佳实践和业务规则
4. **知识可积累**: 每次交互都在丰富业务知识库
