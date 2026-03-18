# GoldMiner - 智能数据分析 Agent

> 🎯 **一句话介绍**：基于 LLM 的自动化数据分析助手，通过自然语言交互完成 MaxCompute SQL 查询与报告生成

---

## 📌 项目概述

GoldMiner 是一个轻量级、OpenClaw 风格的 AI Agent，专为**广告投放数据分析**场景设计。它能够：

- 🤖 **智能理解**：通过自然语言理解用户的分析需求
- 📝 **自动生成 SQL**：基于业务知识生成准确的 MaxCompute SQL
- ⚡ **执行查询**：通过 PyODPS 执行 SQL 并获取结果
- 📊 **生成报告**：自动整理分析结果并输出 Markdown 报告
- 🧠 **记忆持久化**：保存对话历史，支持上下文理解

### 核心能力

| 能力 | 说明 |
|------|------|
| **自然语言交互** | 用户用中文描述分析需求，Agent 自动理解并执行 |
| **智能表匹配** | 自动从 skills/maxcompute 目录匹配相关数据表 |
| **业务知识融合** | 内置广告投放业务术语和表结构知识 |
| **SQL 生成优化** | 基于表分区信息自动生成高效查询 |
| **任务可取消** | 支持实时取消正在执行的 SQL 任务 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户交互层                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ CLI 模式 │  │ Web 界面 │  │ 飞书 Bot │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Agent 核心层                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  Agent (ReAct 循环)                  │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │    │
│  │  │ Thought │→│  Action │→│Execute  │→│Observe │ │    │
│  │  │  思考   │  │  行动   │  │ 执行    │  │ 观察   │ │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   LLM 服务层     │ │   业务知识层     │ │   数据执行层     │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │  LLM API  │  │ │  │ 术语表    │  │ │  │ PyODPS    │  │
│  │ (GPT/Kimi)│  │ │  │ 表结构    │  │ │  │ MaxCompute│  │
│  └───────────┘  │ │  │ 查询规则  │  │ │  └───────────┘  │
└─────────────────┘ │  └───────────┘  │ └─────────────────┘
                    └─────────────────┘
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
python -m gold_miner.cli

# 示例对话
> 查询昨天广告投放的消耗数据
> 分析贷款CVR模型的特征分布
> /cancel  # 取消当前任务
> /reset   # 清空对话历史
> quit     # 退出
```

**Web 模式：**
```bash
python -m gold_miner.web_server
# 访问 http://localhost:5000
```

---

## 💡 使用场景示例

### 场景 1：广告消耗分析

**用户输入：**
```
查询昨天各广告账户的消耗情况，按消耗降序排列
```

**Agent 执行：**
1. 🔍 自动匹配表：`mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi`
2. 📝 生成 SQL：
   ```sql
   SELECT account_id, 
          SUM(billing_actual_deduction_price)/1e5 AS spend_cost
   FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi
   WHERE dh >= '2026031600' AND dh <= '2026031623'
   GROUP BY account_id
   ORDER BY spend_cost DESC
   LIMIT 100
   ```
3. ⚡ 执行查询
4. 📊 生成报告

### 场景 2：贷款 CVR 模型分析

**用户输入：**
```
分析贷款CVR模型的训练数据，统计各标签的样本分布
```

**Agent 执行：**
1. 🔍 自动匹配表：`mi_ads_dmp.dwd_dld_loancvr_model_train_data_di`
2. 📝 生成 SQL 分析标签分布
3. 📈 生成可视化报告

---

## 📁 项目结构

```
GoldMiner/
├── src/gold_miner/           # 核心源码
│   ├── agent.py              # Agent 主逻辑
│   ├── llm.py                # LLM 客户端
│   ├── odps_client.py        # MaxCompute 客户端
│   ├── business_knowledge.py # 业务知识管理
│   ├── cli.py                # 命令行界面
│   └── web_server.py         # Web 服务
│
├── skills/                   # Skill 插件目录
│   ├── maxcompute/           # 数据表 Skill
│   │   ├── table_dwd_ew_ads_show_res_clk_dld_conv_hi/
│   │   └── table_mi_ads_dmp_dwd_dld_loancvr_model_train_data_di/
│   ├── maxcompute-sql/       # SQL 分析 Skill
│   ├── feishu_notify/        # 飞书通知 Skill
│   └── tavily_search/        # 搜索 Skill
│
├── knowledge/                # 业务知识库
│   ├── glossary/             # 术语表
│   ├── tables/               # 表结构知识
│   └── rules/                # 查询规则
│
├── memory/                   # 记忆存储
├── reports/                  # 报告输出
├── tests/                    # 测试用例
├── .env.example              # 环境变量示例
└── README.md
```

---

## 🔧 核心功能详解

### 1. 智能表匹配

当用户未指定表名时，Agent 会自动：

1. **扫描 skills/maxcompute 目录** - 发现可用数据表
2. **语义匹配** - 根据问题内容匹配相关表
3. **加载表结构** - 自动提取字段、分区信息

**匹配示例：**
| 用户问题 | 匹配表 |
|---------|--------|
| 查询广告展示点击数据 | `dwd_ew_ads_show_res_clk_dld_conv_hi` |
| 分析贷款CVR模型 | `dwd_dld_loancvr_model_train_data_di` |
| 查看创意素材 | `dim_creativity_dd` |

### 2. 业务知识融合

```yaml
# knowledge/glossary/core_terms.yaml
业务术语:
  消耗:
    英文: Spend / Cost
    定义: 广告投放实际扣费金额
    计算公式: billing_actual_deduction_price / 100000
    
  CVR:
    英文: Conversion Rate
    定义: 转化率 = 转化数 / 点击数
    计算公式: conversion_count / click_count
```

### 3. 记忆系统

- **短期记忆**：当前对话的完整历史
- **长期记忆**：历史对话的摘要总结
- **持久化存储**：自动保存到 `memory/memory.json`

### 4. Skill 系统

Skill 是可插拔的功能模块：

```python
# skills/basic_stats.py
SKILL = {
    "name": "calc_summary_stats",
    "description": "计算数值列的统计摘要",
    "inputs": {
        "column": "数值列名"
    },
    "run": lambda df, column: df[column].describe()
}
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
- `glossary/*.yaml` - 业务术语定义
- `tables/*.yaml` - 表结构知识
- `rules/*.yaml` - 查询规则

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_cli_chat.py -v
pytest tests/test_skill_integration.py -v
```

---

## 📝 开发计划

- [x] 基础 Agent 框架
- [x] MaxCompute SQL 执行
- [x] 业务知识管理
- [x] 智能表匹配
- [x] CLI 交互界面
- [x] Web 服务
- [x] 飞书 Bot 集成
- [ ] 更多数据源支持
- [ ] 可视化图表生成
- [ ] 权限管理系统

---

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支：`git checkout -b feature/xxx`
3. 提交更改：`git commit -am 'Add xxx'`
4. 推送分支：`git push origin feature/xxx`
5. 创建 Pull Request

---

## 📄 许可证

MIT License

---

## 💬 联系方式

- 项目地址：https://github.com/chenliulian/Gold-Miner
- 问题反馈：[Issues](https://github.com/chenliulian/Gold-Miner/issues)

---

> 💡 **提示**：首次使用建议先阅读 `docs/business_knowledge_system.md` 了解业务知识管理系统的详细设计。
