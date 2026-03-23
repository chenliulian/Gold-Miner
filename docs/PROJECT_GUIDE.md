# GoldMiner - 智能数据分析 Agent 完整指南

> 🎯 **一句话介绍**：基于 LLM 的自动化数据分析助手，通过自然语言交互完成 MaxCompute SQL 查询、Skill 调用与报告生成

---

## 📌 项目概述

GoldMiner 是一个轻量级、OpenClaw 风格的 AI Agent，专为**广告投放数据分析**场景设计。它深度融合了业务知识库与 Skill 系统，能够：

- 🤖 **智能理解**：通过自然语言理解复杂的分析需求
- 📝 **自动生成 SQL**：基于业务知识生成准确的 MaxCompute SQL
- 🧩 **Skill 编排**：调用 20+ 个专业 Skill 完成复杂分析任务
- ⚡ **执行查询**：通过 PyODPS 执行 SQL 并获取结果
- 📊 **生成报告**：自动整理分析结果并输出结构化报告
- 🧠 **知识沉淀**：持续积累表结构、ETL 逻辑、业务规则等知识

### 核心能力

| 能力 | 说明 |
|------|------|
| **自然语言交互** | 用户用中文描述分析需求，Agent 自动理解并执行 |
| **智能表匹配** | 自动从 knowledge/tables 匹配相关数据表 |
| **业务知识融合** | 内置广告投放业务术语、表结构、ETL 逻辑知识 |
| **Skill 编排** | 支持 20+ 个专业 Skill，覆盖漏斗分析、模型评估、数据探索等 |
| **SQL 生成优化** | 基于表分区信息自动生成高效查询 |
| **任务可取消** | 支持实时取消正在执行的 SQL 任务 |
| **记忆持久化** | 保存对话历史，支持上下文理解 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户交互层                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                              │
│  │ CLI 模式 │  │ Web 界面 │  │ 飞书 Bot │                              │
│  └──────────┘  └──────────┘  └──────────┘                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Agent 核心层                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     Agent (ReAct 循环)                           │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────────────────┐ │    │
│  │  │ Thought │→│  Action │→│Execute  │→│ Observe & Learn    │ │    │
│  │  │  思考   │  │  行动   │  │ 执行    │  │ 观察与知识沉淀      │ │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│   LLM 服务层     │     │    业务知识层        │     │   数据执行层     │
│  ┌───────────┐  │     │  ┌───────────────┐  │     │  ┌───────────┐  │
│  │  LLM API  │  │     │  │  表结构知识    │  │     │  │ PyODPS    │  │
│  │ (GPT/Kimi)│  │     │  │  ETL 逻辑      │  │     │  │MaxCompute │  │
│  └───────────┘  │     │  │  字段业务含义  │  │     │  └───────────┘  │
└─────────────────┘     │  ├───────────────┤  │     └─────────────────┘
                        │  │  业务术语表    │  │
                        │  │  查询规则      │  │
                        │  └───────────────┘  │
                        └─────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Skill 系统层                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ 数据分析 Skill│ │ 数据探索 Skill│ │ 通知服务 Skill│ │ 系统工具 Skill│   │
│  │ 漏斗分析      │ │ 表结构探索    │ │ 飞书通知      │ │ 任务规划      │   │
│  │ PCOC 分析     │ │ 血缘分析      │ │ 搜索服务      │ │ 系统命令      │   │
│  │ 模型评估      │ │ 对话检索      │ │ 记忆更新      │ │ 自我改进      │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/chenliulian/Gold-Miner.git
cd Gold-Miner

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e .
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件，填写以下关键配置
```

**核心配置项：**

```ini
# LLM API 配置
LLM_BASE_URL=https://your-llm-endpoint.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4o

# MaxCompute/ODPS 配置
ODPS_ACCESS_ID=your-access-id
ODPS_ACCESS_KEY=your-access-key
ODPS_PROJECT=your-project-name
ODPS_ENDPOINT=http://service.eu-central-1.maxcompute.aliyun.com/api
```

### 3. 运行示例

**CLI 模式：**
```bash
# 启动交互式聊天
gold-miner chat
# 或
python -m gold_miner.cli

# 示例对话
> 查询昨天广告投放的消耗数据
> 分析广告组 70711 的投放漏斗
> 计算贷款CVR模型的PCOC偏差
> /cancel  # 取消当前任务
> /reset   # 清空对话历史
> quit     # 退出
```

**Web 模式：**
```bash
cd ui
python app.py
# 访问 http://localhost:5000
```

---

## 🧩 Skill 系统详解

GoldMiner 内置 20+ 个专业 Skill，分为四大类别：

### 1. 数据分析 Skill

| Skill 名称 | 功能描述 | 使用场景 |
|-----------|---------|---------|
| `adgroup_funnel_analysis` | 广告组投放漏斗分析 | 分析从召回到转化的完整链路 |
| `analyze_ctr_pcoc` | CTR 模型 PCOC 分析 | 评估 CTR 模型预估偏差 |
| `analyze_cvr_pcoc` | CVR 模型 PCOC 分析 | 评估 CVR 模型预估偏差 |
| `calc_summary_stats` | 汇总统计计算 | 计算消耗、CTR、CVR 等指标 |
| `calc_model_mae` | 模型 MAE 计算 | 计算模型预测的平均绝对误差 |
| `build_adgroup_data` | 广告组数据构建 | 构建 adgroup 维度的中间聚合表 |

### 2. 数据探索 Skill

| Skill 名称 | 功能描述 | 使用场景 |
|-----------|---------|---------|
| `explore_table` | 表结构探索 | 自动获取表结构、字段注释、样本数据 |
| `explore_table_lineage` | 血缘分析 | 通过 DataWorks 获取表的血缘关系 |
| `search_conversation` | 对话检索 | 检索历史对话记录 |
| `basic_stats` | 基础统计 | 计算数值列的统计摘要 |

### 3. 通知服务 Skill

| Skill 名称 | 功能描述 | 使用场景 |
|-----------|---------|---------|
| `feishu_notify` | 飞书通知 | 发送分析结果到飞书 |
| `feishu_server` | 飞书服务 | 飞书 Bot 服务端 |
| `tavily_search` | 网络搜索 | 使用 Tavily 搜索技术资料 |

### 4. 系统工具 Skill

| Skill 名称 | 功能描述 | 使用场景 |
|-----------|---------|---------|
| `task_planner` | 任务规划 | 规划复杂数据分析任务 |
| `system_command` | 系统命令 | 执行文件检索、目录操作等 |
| `update_memory` | 记忆更新 | 更新结构化记忆文件 |
| `create_skill` | Skill 创建 | 根据需求自动创建新 Skill |
| `self_improvement` | 自我改进 | 记录错误和学习点 |
| `heartbeat` | 心跳检测 | 服务健康检查 |

### Skill 使用示例

```python
# 调用 adgroup_funnel_analysis Skill
result = agent.skills.call("adgroup_funnel_analysis",
    ad_group_id="70711",
    start_dh="2026031500",
    end_dh="2026031523",
    analysis_type="full_funnel"
)

# 调用 explore_table Skill
result = agent.skills.call("explore_table",
    table_name="dwd_ew_ads_show_res_clk_dld_conv_hi",
    project="mi_ads_dmp",
    sample_rows=5
)
```

---

## 📚 业务知识系统

GoldMiner 的业务知识系统包含三个核心层次：

### 1. 表结构知识 (knowledge/tables/)

每个数据表都有详细的 YAML 知识文件，包含：

```yaml
表名: mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
业务名称: 广告曝光响应点击下载转化明细小时表
数据粒度: 曝光/点击/下载/转化事件明细
更新频率: 小时
保留周期: 90天

列信息:
  - 列名: request_id
    类型: STRING
    业务含义: 广告请求ID，唯一标识一次广告请求
    
  - 列名: show_label
    类型: BIGINT
    业务含义: 是否曝光，1=曝光，0=未曝光
    
  - 列名: click_label
    类型: BIGINT
    业务含义: 是否点击，1=点击，0=未点击
    
  - 列名: billing_actual_deduction_price
    类型: BIGINT
    业务含义: 实际扣费金额，单位：微美元（需除以1e5转为美元）
    
  - 列名: ctr
    类型: DOUBLE
    业务含义: 预估点击率（校准后）
    
  - 列名: cvr
    类型: DOUBLE
    业务含义: 预估转化率（校准后）

数据生产逻辑:
  - 曝光数据来自广告引擎响应日志
  - 点击数据通过归因服务关联
  - 下载/转化数据通过归因链路回传
  - 严格分层：曝光 left join 点击 left join 转化
```

### 2. ETL 逻辑知识 (knowledge/etl/)

包含核心表的 ETL SQL 代码：

```sql
-- ads_strategy_dwd_ads_competition_rank_hi 的 ETL 逻辑
-- 1. 从竞价服务获取竞价记录
-- 2. 关联广告组维度信息
-- 3. 计算排名位次和胜出价格
-- 4. 写入分区表
```

### 3. 业务术语表 (knowledge/glossary/)

```yaml
业务术语:
  消耗:
    英文: spend / cost
    定义: 广告投放实际扣费金额
    计算公式: billing_actual_deduction_price / 1e5 (转为美元)
    
  CTR:
    英文: Click Through Rate
    定义: 点击率 = 点击数 / 曝光数
    计算公式: click_count / show_count
    
  CVR:
    英文: Conversion Rate
    定义: 转化率 = 转化数 / 点击数
    计算公式: conversion_count / click_count
    
  PCOC:
    英文: Predicted Click Over Click
    定义: 预估CTR与实际CTR的比值
    计算公式: pCTR / 实际CTR
    解读: =1准确, >1高估, <1低估
```

---

## 💡 使用场景示例

### 场景 1：广告组漏斗分析

**用户输入：**
```
分析广告组 70711 在 2026-03-15 的投放漏斗数据
```

**Agent 执行：**
1. 🔍 调用 `adgroup_funnel_analysis` Skill
2. 📝 生成多维度 SQL：
   - 全链路漏斗（召回→过滤→精排→响应→曝光→点击→转化）
   - 消耗数据分析
   - CTR/CVR PCOC 模型偏差分析
   - 竞胜率分析
3. ⚡ 执行查询并汇总结果
4. 📊 生成结构化报告

**输出示例：**
```markdown
## 广告组 70711 投放漏斗分析

### 1. 全链路漏斗
| 阶段 | 数量 | 转化率 |
|-----|------|-------|
| 召回 | 125,000 | - |
| 进精排 | 45,000 | 36.0% |
| 响应 | 12,000 | 26.7% |
| 曝光 | 11,500 | 95.8% |
| 点击 | 345 | 3.0% |
| 转化 | 28 | 8.1% |

### 2. 消耗数据
- 总消耗: $45.67
- CPC: $0.132
- CPM: $3.97

### 3. 模型偏差分析
- CTR PCOC: 1.05 (轻度高估)
- CVR PCOC: 0.92 (轻度低估)
```

### 场景 2：模型 PCOC 分析

**用户输入：**
```
分析贷款CVR模型在 2026-03-15 的预估偏差
```

**Agent 执行：**
1. 🔍 调用 `analyze_cvr_pcoc` Skill
2. 📝 生成 PCOC 分析 SQL
3. 📊 计算各维度 PCOC 值
4. 📈 生成偏差分布报告

### 场景 3：表结构探索

**用户输入：**
```
探索 mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi 表结构
```

**Agent 执行：**
1. 🔍 调用 `explore_table` Skill
2. 📝 获取表结构、字段注释、样本数据
3. 📊 自动识别 ID 字段、标签字段、计费字段、时间字段
4. 💾 生成/更新 knowledge/tables YAML 文件

---

## 📁 项目结构

```
GoldMiner/
├── src/gold_miner/              # 核心源码
│   ├── agent.py                 # Agent 主逻辑 (ReAct 循环)
│   ├── skills.py                # Skill 注册与调用
│   ├── business_knowledge.py    # 业务知识管理
│   ├── odps_client.py           # MaxCompute 客户端
│   ├── llm.py                   # LLM 客户端
│   ├── memory.py                # 记忆系统
│   ├── cli.py                   # 命令行界面
│   └── web_server.py            # Web 服务
│
├── skills/                      # Skill 插件目录
│   ├── adgroup_funnel_analysis/ # 广告组漏斗分析
│   ├── maxcompute-sql/          # MaxCompute SQL Skill
│   ├── explore_table/           # 表结构探索
│   ├── search_conversation/     # 对话检索
│   ├── task_planner/            # 任务规划
│   ├── feishu_notify/           # 飞书通知
│   └── ...                      # 其他 Skills
│
├── knowledge/                   # 业务知识库
│   ├── tables/                  # 表结构知识 (YAML)
│   ├── etl/                     # ETL 逻辑 (SQL)
│   ├── glossary/                # 业务术语表
│   └── scripts/                 # 知识更新脚本
│
├── memory/                      # 记忆存储
├── reports/                     # 报告输出
├── tests/                       # 测试用例
├── docs/                        # 文档
│   ├── PROJECT_GUIDE.md         # 项目完整指南 (本文档)
│   └── business_knowledge_system.md  # 业务知识系统设计
├── .env.example                 # 环境变量示例
└── README.md                    # 项目简介
```

---

## ⚙️ 配置说明

### 环境变量 (.env)

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `LLM_BASE_URL` | LLM API 地址 | ✅ |
| `LLM_API_KEY` | LLM API 密钥 | ✅ |
| `LLM_MODEL` | 模型名称 | ✅ |
| `ODPS_ACCESS_ID` | MaxCompute Access ID | ✅ |
| `ODPS_ACCESS_KEY` | MaxCompute Access Key | ✅ |
| `ODPS_PROJECT` | MaxCompute 项目名 | ✅ |
| `ODPS_ENDPOINT` | MaxCompute 端点 | ✅ |
| `ODPS_QUOTA` | Quota 名称 | ❌ |
| `AGENT_MAX_STEPS` | 最大执行步数 | ❌ |
| `FEISHU_APP_ID` | 飞书应用 ID | ❌ |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | ❌ |

### 业务知识配置

在 `knowledge/` 目录下添加：
- `tables/*.yaml` - 表结构知识
- `etl/*.sql` - ETL 逻辑
- `glossary/*.yaml` - 业务术语定义

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_cli_chat.py -v
pytest tests/test_skill_integration.py -v
pytest tests/test_skills.py -v

# 测试 Skill 加载
python test_skills_loading.py
```

---

## 📝 开发计划

- [x] 基础 Agent 框架 (ReAct 循环)
- [x] MaxCompute SQL 执行
- [x] 业务知识管理系统
- [x] Skill 系统 (20+ Skills)
- [x] 智能表匹配
- [x] CLI 交互界面
- [x] Web 服务
- [x] 飞书 Bot 集成
- [x] 广告漏斗分析 Skill
- [x] 模型 PCOC 分析 Skill
- [ ] 可视化图表生成
- [ ] 权限管理系统
- [ ] 更多数据源支持 (Hive, ClickHouse)

---

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支：`git checkout -b feature/xxx`
3. 提交更改：`git commit -am 'Add xxx'`
4. 推送分支：`git push origin feature/xxx`
5. 创建 Pull Request

### 添加新 Skill

```python
# skills/my_skill/my_skill.py

def run(param1: str, param2: int = 10) -> dict:
    """
    Skill 功能描述
    
    参数:
        param1: 参数1说明
        param2: 参数2说明 (默认 10)
    """
    # 实现逻辑
    return {
        "success": True,
        "result": "..."
    }

SKILL = {
    "name": "my_skill",
    "description": "Skill 描述",
    "inputs": {
        "param1": "str - 参数1",
        "param2": "int (可选) - 参数2，默认 10",
    },
    "run": run,
}
```

---

## 📄 许可证

MIT License

---

## 💬 联系方式

- 项目地址：https://github.com/chenliulian/Gold-Miner
- 问题反馈：[Issues](https://github.com/chenliulian/Gold-Miner/issues)

