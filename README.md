# GoldMiner - 智能数据分析 Agent

> 🎯 **一句话介绍**：基于 LLM 的自动化数据分析助手，通过自然语言交互完成 MaxCompute SQL 查询、Skill 调用与报告生成。**Agent 能记住用户强调的业务背景知识，越用越懂你的业务。**

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🤖 **自然语言交互** | 用中文描述分析需求，Agent 自动理解并执行 |
| 🧠 **长期记忆** | 记住表结构、指标定义、业务背景（用户说"记住"即可） |
| 📚 **业务知识库** | 内置广告投放业务术语、表结构、ETL 逻辑 |
| 📝 **智能 SQL 生成** | 基于业务知识生成准确的 MaxCompute SQL |
| 🧩 **Skill 编排** | 调用 20+ 个专业 Skill 完成复杂分析任务 |
| 👥 **多用户支持** | 用户隔离的记忆空间和数据权限 |
| 🔐 **企业级认证** | 飞书 SSO + 本地登录 + JWT Token |
| ⚡ **高可用架构** | 多 LLM Provider 自动故障转移 + Agent 池化 |

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
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填写以下必填项
```

**关键配置项说明**：

> 📋 **配置方式说明**
> - **Web UI 模式**：以下 LLM 和 ODPS 配置为可选，用户登录后在界面配置个人 API 密钥
> - **CLI 模式**：以下配置为必填，通过 `.env` 文件配置全局 API 密钥

```bash
# =============================================================================
# 安全相关配置（必须配置，否则无法启动 - 适用于所有模式）
# =============================================================================
# JWT 密钥 - 用于签名认证令牌，至少 32 字符
# 生成示例: openssl rand -hex 32
JWT_SECRET=your-jwt-secret-min-32-chars-long

# 会话密钥 - 用于 Flask 会话加密，至少 32 字符
SESSION_SECRET=your-secure-random-session-secret-min-32-chars-long

# 用户 API 密钥加密密钥
USER_API_KEY_ENCRYPTION_KEY=your-encryption-key

# =============================================================================
# LLM API 配置（CLI 模式必填；Web UI 模式可选，用户可在界面配置）
# =============================================================================
# 主用 LLM
LLM_BASE_URL=https://your-llm-api-endpoint.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o

# 备用 LLM（可选，主用失败时自动切换）
LLM_BASE_URL_backup1=https://backup-llm-api.com/v1
LLM_API_KEY_backup1=your-backup-api-key
LLM_MODEL_backup1=gpt-4o-mini

# =============================================================================
# MaxCompute / ODPS 配置（CLI 模式必填；Web UI 模式可选，用户可在界面配置）
# =============================================================================
ODPS_ACCESS_ID=your-access-id
ODPS_ACCESS_KEY=your-access-key
ODPS_PROJECT=your-project-name
ODPS_ENDPOINT=http://service.eu-central-1.maxcompute.aliyun.com/api

# =============================================================================
# 飞书 SSO 配置（可选，用于飞书登录）
# =============================================================================
FEISHU_APP_ID=your-feishu-app-id
FEISHU_APP_SECRET=your-feishu-app-secret
FEISHU_REDIRECT_URI=http://localhost:5000/auth/feishu/callback
```

### 3. 启动服务

#### Web UI 模式（推荐）

```bash
cd ui && python app.py
```

然后打开浏览器访问 `http://localhost:5000`

**⚠️ 重要提示：首次登录后需要配置 API 密钥**

Web UI 模式采用**多用户隔离架构**，每个用户需要独立配置自己的 API 密钥：

1. **注册/登录账号** - 使用本地账号或飞书 SSO 登录
2. **配置 LLM API** - 在「设置」页面填写您的 LLM API Key 和 Base URL
3. **配置 ODPS API** - 在「设置」页面填写您的 MaxCompute Access ID/Key 和 Project

> 💡 **为什么需要独立配置？** 每个用户的 API 密钥独立存储和加密，确保数据隔离和安全性。管理员无需在服务器上配置全局 API 密钥。

---

#### CLI 模式

```bash
gold-miner chat
```

CLI 模式采用**单用户模式**，可以直接通过 `.env` 文件配置 API 密钥（见上方配置说明），适合个人本地使用。

---

## 🧠 记忆系统详解

GoldMiner 的核心能力之一是**能够记住用户强调的业务背景知识**，并在后续分析中自动应用。

### 记忆类型

| 记忆类型 | 说明 | 触发方式 |
|---------|------|---------|
| **表结构记忆** | 保存常用表的字段结构 | 用户说"记住这个表结构" |
| **指标定义记忆** | 保存指标的业务口径和计算公式 | 用户说"保存这个指标定义" |
| **业务背景记忆** | 保存行业知识、分析偏好等 | 用户说"记住这个业务背景" |
| **对话要点记忆** | 保存关键分析结论 | 用户说"记下来" |

### 使用示例

**示例 1：记住表结构**

```
用户：帮我分析一下昨天广告组的消耗
Agent：已为您查询到消耗数据，共 15 个广告组，总消耗 $12,345...
用户：记住这个表结构，以后分析都用这个表
Agent：✓ 已保存表结构 com_cdm_dws_tracker_ad_cpc_cost_hi 到长期记忆
       包含字段：ad_group_id, cost, impression, click, conversion...

[后续对话]
用户：再看下前天的消耗
Agent：[自动使用记住的表结构，无需再次询问] 已为您查询到前天数据...
```

**示例 2：记住指标定义**

```
用户：计算一下 ROI
Agent：ROI = 收入 / 消耗，已为您计算...
用户：保存这个指标定义，我们团队的 ROI 口径是 LTV7 / 消耗
Agent：✓ 已保存指标定义 "ROI" = "LTV7 / 消耗" 到长期记忆

[后续对话]
用户：分析下广告组 70711 的 ROI
Agent：[自动使用记住的 ROI 口径] 使用 LTV7 / 消耗 计算...
```

**示例 3：记住业务背景**

```
用户：记住这个业务背景，我们是大客户团队，只关注消耗 > $1000 的广告组
Agent：✓ 已保存业务背景到长期记忆

[后续对话]
用户：分析下昨天的广告组表现
Agent：[自动应用业务背景] 已筛选出消耗 > $1000 的广告组...
```

### 记忆管理

- **多用户隔离**：每个用户有自己的记忆空间，互不影响
- **自动摘要**：生成可读的 Markdown 摘要文档
- **持久化存储**：记忆保存在 `data/users/{user_id}/memory/` 目录
- **查看记忆**：通过 Web UI 或 `search_conversation` Skill 查看

---

## 📚 业务知识库

GoldMiner 内置了完整的业务知识库，帮助 Agent 理解广告投放领域的专业概念。

### 知识库结构

```
knowledge/
├── glossary/          # 业务术语词典
│   ├── core_terms.yaml      # 核心指标定义（消耗、展示、点击、转化等）
│   └── ad_engine_architecture.yaml  # 广告引擎架构知识
├── tables/            # 表结构知识（15+ 张核心表）
│   ├── com_cdm_dws_tracker_ad_cpc_cost_hi.yaml  # 黄金眼底表
│   ├── com_cdm_dim_ad_group_dd.yaml             # 广告组维度表
│   └── ...  # 其他业务表
└── rules/             # 查询规则
    └── query_rules.yaml       # SQL 编写规范、最佳实践
```

### 知识库如何工作

1. **用户提问**："分析一下广告组 70711 的投放漏斗"

2. **知识检索**：
   - 从 `glossary` 匹配"广告组"、"漏斗"等业务术语
   - 从 `tables` 匹配相关表（如 `dim_ad_group_dd`、`dws_tracker_ad_cpc_cost_hi`）
   - 从 `rules` 加载查询规则（如"必须带分区条件"）

3. **生成 SQL**：
   - 基于表结构知识知道有哪些字段可用
   - 基于业务术语理解指标计算方式
   - 应用查询规则生成高效 SQL

4. **执行与报告**：执行 SQL 并生成分析报告

### 扩展知识库

你可以通过以下方式扩展知识库：

1. **添加新表知识**：在 `knowledge/tables/` 下创建 YAML 文件
2. **添加业务术语**：在 `knowledge/glossary/core_terms.yaml` 中添加
3. **添加查询规则**：在 `knowledge/rules/query_rules.yaml` 中添加

---

## 🔐 用户认证系统

GoldMiner 支持多种认证方式：

### 1. 飞书 SSO 登录

用户可以使用飞书账号扫码登录，适合企业环境。

**配置步骤**：
1. 在飞书开放平台创建应用
2. 配置 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_REDIRECT_URI`
3. 用户访问登录页面，选择"飞书登录"

### 2. 本地用户登录

支持传统的用户名/密码登录。

**管理员创建用户**：
```bash
# 通过 API 或数据库直接创建用户
```

### 3. 认证流程

```
用户访问 → 检查登录状态 → 未登录 → 跳转登录页
                              ↓
                        选择登录方式
                        ↙         ↘
                  飞书 SSO    本地登录
                        ↓         ↓
                  飞书授权    验证密码
                        ↓         ↓
                        生成 JWT Token
                              ↓
                        访问受保护资源
```

---

## ⚙️ 高级配置

### Agent Pool 配置

```bash
# Agent 池最小数量（保持预热）
AGENT_POOL_MIN_SIZE=2

# Agent 池最大数量（限制并发）
AGENT_POOL_MAX_SIZE=10

# Agent 最大空闲时间（秒）
AGENT_POOL_MAX_IDLE_TIME=3600
```

### 限流配置

```bash
# 默认限流：每分钟请求数
RATE_LIMIT_DEFAULT_PER_MINUTE=60

# 聊天限流：每分钟请求数
RATE_LIMIT_CHAT_PER_MINUTE=10
```

### 熔断器配置

```bash
# 熔断器触发失败次数阈值
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5

# 熔断器恢复超时时间（秒）
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=30
```

---

## 🛠️ Skill 系统

GoldMiner 通过 Skill 系统扩展能力，目前内置 20+ 个专业 Skill。

### Skill 分类

| 分类 | Skill | 说明 |
|------|-------|------|
| **数据分析** | `adgroup_funnel_analysis` | 广告组漏斗分析 |
| | `analyze_ctr_pcoc` | CTR PCOC 偏差分析 |
| | `analyze_cvr_pcoc` | CVR PCOC 偏差分析 |
| | `calc_model_mae` | 模型 MAE 计算 |
| | `monitor_ltv_roi` | LTV/ROI 监控 |
| | `roas_bias` | ROAS 偏差分析 |
| **数据探索** | `explore_table` | 表结构探索 |
| | `explore_table_lineage` | 表血缘分析 |
| **通知服务** | `feishu_notify` | 飞书消息通知 |
| | `feishu_server` | 飞书机器人服务 |
| **系统工具** | `task_planner` | 任务规划 |
| | `system_command` | 系统命令执行 |
| | `self_improvement` | 自我改进/学习 |
| | `update_memory` | 更新长期记忆 |
| | `search_conversation` | 对话历史检索 |
| | `tavily_search` | Tavily 搜索 |
| | `create_skill` | 创建新 Skill |

### 开发新 Skill

参考 `skills/create_skill/SKILL.md` 了解如何开发自定义 Skill。

---

## 📦 部署指南

### 生产环境部署

项目提供了完整的部署脚本：

```bash
# 1. 准备服务器（阿里云 ECS 推荐）

# 2. 运行部署脚本
cd deploy
./ecs_deploy.sh

# 3. 配置 systemd 服务
./ecs_setup_service.sh
```

详细部署说明请参考 `deploy/README.md`。

---

## 📝 完整使用示例

```
🤖 GoldMiner Chat Mode
Type your question or use commands:
  /cancel - Cancel current task
  /reset  - Clear conversation history
  quit    - Exit

> 查询昨天广告投放的消耗数据
[Agent 自动匹配表结构并生成 SQL]
📊 查询结果：
   总消耗：$45,678
   展示次数：1,234,567
   点击次数：45,678
   转化次数：1,234

> 记住这个表结构，以后都用这个表分析
✓ 已保存表结构到长期记忆

> 分析一下广告组 70711 的投放漏斗
[Agent 调用 funnel_analysis Skill]
📈 漏斗分析结果：
   展示 → 点击：3.7%
   点击 → 转化：2.7%
   整体转化率：0.1%

> 保存这个漏斗定义，我们关注的漏斗是 展示→点击→下载→激活
✓ 已保存业务背景到长期记忆

> 计算贷款 CVR 模型的 PCOC 偏差
[Agent 调用 analyze_cvr_pcoc Skill]
📊 PCOC 分析结果：
   模型预测 CVR：2.5%
   实际 CVR：2.3%
   PCOC 偏差：-8%

> 记下来，模型在贷款场景下有低估倾向
✓ 已保存对话要点到长期记忆

> /cancel
Task cancelled.

> /reset
Conversation history cleared.

> quit
Goodbye!
```

---

## 📁 项目结构

```
gold-miner/
├── src/gold_miner/          # 核心代码
│   ├── auth/                # 认证模块
│   ├── services/            # 服务层（Agent Pool、任务队列）
│   ├── agent.py             # Agent 核心
│   ├── memory.py            # 长期记忆管理
│   ├── business_knowledge.py # 业务知识管理
│   └── ...
├── skills/                  # Skill 目录（20+ Skills）
├── knowledge/               # 业务知识库
│   ├── glossary/            # 术语词典
│   ├── tables/              # 表结构知识
│   └── rules/               # 查询规则
├── system_prompts/          # 系统提示词
├── ui/                      # Web UI
│   ├── templates/           # HTML 模板
│   ├── app.py               # Flask 应用
│   └── api_v2.py            # API 接口
├── deploy/                  # 部署脚本
├── docs/                    # 架构文档
└── memory/                  # 记忆存储（运行时生成）
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 PR！

---

## 📄 License

MIT License
