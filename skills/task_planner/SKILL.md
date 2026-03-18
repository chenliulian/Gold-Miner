# Task Planner - 业务数据洞察分析任务规划器

## 概述

Task Planner 是一个专门用于业务数据洞察分析的智能化任务规划 Skill。它能够：

- **自动识别分析模式**：根据业务问题自动识别分析类型（趋势、对比、归因、漏斗等）
- **智能任务拆解**：将复杂的分析需求拆解为可执行的任务序列
- **依赖关系管理**：自动处理任务间的依赖关系，确保正确执行顺序
- **执行状态跟踪**：支持任务状态跟踪和结果汇总

## 使用场景

### 1. 趋势分析
```python
from skills.task_planner.task_planner import run

result = run(
    business_question="分析过去30天广告CTR的趋势变化，识别异常波动日期",
    tables=["mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi"],
    analysis_depth="standard",
)
```

### 2. 对比分析
```python
result = run(
    business_question="对比不同创意类型（图片vs视频）的转化率和成本差异",
    tables=["mi_ads_dmp.dwd_dld_loancvr_model_train_data_di", "com_cdm.dim_creativity_dd"],
    analysis_depth="deep",
)
```

### 3. 归因分析
```python
result = run(
    business_question="分析3月15日CTR突然下降的原因，按广告位和定向维度拆解",
    tables=["mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi"],
    analysis_depth="deep",
)
```

### 4. 漏斗分析
```python
result = run(
    business_question="分析广告曝光->点击->下载->激活的转化漏斗，找出主要流失环节",
    tables=["mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi"],
    analysis_depth="standard",
)
```

## 支持的参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `business_question` | str | 是 | - | 业务问题或分析目标 |
| `tables` | List[str] | 否 | [] | 涉及的表名列表 |
| `analysis_depth` | str | 否 | "standard" | 分析深度: quick/standard/deep |
| `output_format` | str | 否 | "markdown" | 输出格式: markdown/json |
| `save_plan` | bool | 否 | True | 是否保存计划到文件 |

## 分析深度说明

### quick (快速分析)
- 仅执行基础数据探查
- 1-2个任务
- 适合快速验证假设

### standard (标准分析)
- 数据探查 + 核心分析 + 数据质量检查
- 3-4个任务
- 适合常规业务分析

### deep (深度分析)
- 完整的数据探查 + 多维度分析 + 深度特征分析 + 综合报告
- 5-6个任务
- 适合重要业务决策支持

## 分析模式识别

Task Planner 能自动识别以下分析模式：

| 模式 | 关键词 | 典型任务 |
|------|--------|----------|
| `trend_analysis` | 趋势、变化、走势、增长、同比、环比 | 时间序列分析、趋势可视化 |
| `comparison_analysis` | 对比、比较、差异、vs | 分组对比、显著性检验 |
| `root_cause_analysis` | 原因、为什么、归因、根因 | 维度下钻、贡献度计算 |
| `segmentation_analysis` | 分层、分群、细分、画像 | 用户分群、特征分析 |
| `correlation_analysis` | 相关、关系、影响、关联 | 相关性分析、回归分析 |
| `prediction_analysis` | 预测、预估、未来 | 趋势预测、模型预测 |
| `funnel_analysis` | 漏斗、转化、流失 | 漏斗步骤统计、流失点识别 |
| `cohort_analysis` | 留存、cohort、同期群 | 留存分析、生命周期分析 |

## 输出示例

### 返回值结构
```python
{
    "success": True,
    "plan_id": "plan_20260318_143052_a1b2c3d4",
    "business_goal": "分析过去30天广告CTR的趋势变化",
    "analysis_pattern": "trend_analysis",
    "analysis_depth": "standard",
    "total_tasks": 4,
    "execution_order": ["task_001", "task_002", "task_003", "task_004"],
    "tasks": [
        {
            "task_id": "task_001",
            "name": "数据概览探查",
            "task_type": "sql",
            "status": "pending",
            "depends_on": [],
            "parameters": {...},
            ...
        },
        ...
    ],
    "plan_document": "# 分析: ...",  # Markdown 格式的完整计划
    "plan_file": "/path/to/plan_xxx.md",
    "message": "分析计划已创建，共 4 个任务..."
}
```

### 生成的计划文档

计划文档包含：
- 分析目标和涉及表
- 详细的任务列表（含依赖关系）
- 每个任务的参数和预期输出
- 执行说明和状态跟踪表

文档保存位置：`plans/plan_{timestamp}_{id}.md`

## 与 Agent 集成

Task Planner 设计为与 GoldMiner Agent 协同工作：

1. **Agent 调用 Task Planner** 创建分析计划
2. **Agent 读取计划** 获取任务列表和执行顺序
3. **Agent 逐个执行任务**（SQL 查询、数据分析等）
4. **Agent 更新任务状态** 并汇总结果
5. **Agent 生成最终报告**

示例 Agent 提示词：
```
你是一个业务数据分析师。当用户提出复杂分析需求时：

1. 首先使用 task_planner skill 创建分析计划
2. 按照计划的执行顺序逐个完成任务
3. 每个任务完成后更新状态
4. 最后汇总所有结果生成综合分析报告

当前分析计划：
{plan_document}
```

## 任务类型

| 类型 | 说明 | 执行方式 |
|------|------|----------|
| `sql` | SQL 查询任务 | 执行 SQL 获取数据 |
| `analysis` | 数据分析任务 | Python/R 分析处理 |
| `visualization` | 可视化任务 | 生成图表 |
| `report` | 报告生成任务 | 汇总生成最终报告 |

## 扩展开发

如需添加新的分析模式或任务模板，修改 `task_planner.py` 中的：

1. `_identify_analysis_pattern()` - 添加新的模式识别关键词
2. `_get_task_templates()` - 添加新的任务模板
3. `Task` 类 - 如需扩展任务属性

## 注意事项

1. 任务依赖关系会自动处理，无需手动指定完整的依赖链
2. 计划文档会保存到 `plans/` 目录，便于后续查看
3. 实际的任务执行需要 Agent 或外部系统调用
4. 建议结合业务知识库（knowledge/tables）使用，自动填充表信息
