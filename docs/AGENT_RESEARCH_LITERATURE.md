# Agent 技术调研文献综述

**版本**: v1.0  
**日期**: 2026-03-24  
**状态**: 调研整理  

---

## 目录

1. [Agent 框架设计核心文献](#一-agent-框架设计核心文献)
2. [Context Engineering 核心文献](#二-context-engineering-核心文献)
3. [Harness Engineering 核心文献](#三-harness-engineering-核心文献)
4. [研究趋势总结](#四-研究趋势总结)

---

## 一、Agent 框架设计核心文献

### 1.1 分层混合智能体架构

| 属性 | 详情 |
|-----|------|
| **发布机构** | Together AI、杜克大学、斯坦福大学 |
| **论文标题** | Mixture-of-Agents Enhances Large Language Model Capabilities |
| **核心主题** | 提出分层混合智能体（MoA）架构，通过多智能体迭代聚合提升模型性能，纯开源方案在 AlpacaEval 2.0 上超越 GPT-4 Omni |
| **发布时间** | 2024 年 6 月 |
| **访问链接** | [arXiv:2406.04692](https://arxiv.org/abs/2406.04692) |

**关键洞察**: MoA 架构通过多层智能体协作，每层智能体基于前一层输出进行迭代优化，最终实现超越单一大型模型的性能。

---

### 1.2 进化式算法智能体

| 属性 | 详情 |
|-----|------|
| **发布机构** | Google DeepMind |
| **论文标题** | AlphaEvolve: A Gemini-Powered Coding Agent for Designing Advanced Algorithms |
| **核心主题** | 提出 LLM 驱动的进化式智能体框架，将算法代码视为基因组，实现自主的算法创新与科学发现，攻克博弈论领域长期存在的算法难题 |
| **发布时间** | 2025 年 6 月（首发）/ 2026 年 2 月（更新） |
| **访问链接** | [arXiv:2602.16928](https://arxiv.org/abs/2602.16928) / [DeepMind Blog](https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/alphaevolve.pdf) |

**关键洞察**: 将进化算法与 LLM 结合，通过代码变异、评估、选择的循环实现算法自动优化，开辟了 AI 辅助科学发现的新范式。

---

### 1.3 类人计算机操作智能体

| 属性 | 详情 |
|-----|------|
| **发布机构** | 斯坦福大学、微软 |
| **论文标题** | Agent S: An Open Agentic Framework that Uses Computers Like a Human |
| **核心主题** | 提出类人计算机操作智能体框架，构建了 "感知 - 规划 - 执行 - 反思" 完整闭环，包含经验增强分层规划器、持续记忆系统与代理 - 计算机接口（ACI） |
| **发布时间** | 2024 年 10 月 |
| **访问链接** | [arXiv:2410.08164](https://arxiv.org/abs/2410.08164) |

**关键洞察**: 通过模拟人类操作计算机的完整认知流程，实现了更鲁棒的 GUI 自动化，经验记忆系统使智能体能够从历史任务中学习。

---

### 1.4 企业级多智能体框架

| 属性 | 详情 |
|-----|------|
| **发布机构** | 通义千问团队 |
| **论文标题** | AgentScope 1.0: A Multi-Agent Framework with High Availability for Enterprise Applications |
| **核心主题** | 开源企业级多智能体开发框架，提供从开发、调试到部署的全流程支持，分层架构设计保障高可用与稳定性 |
| **发布时间** | 2024 年 2 月 |
| **访问链接** | [arXiv:2402.14034](https://arxiv.org/abs/2402.14034) / [GitHub](https://github.com/modelscope/agentscope) |

**关键洞察**: 企业级多智能体系统需要关注高可用性、可观测性和全生命周期管理，分层架构是保障稳定性的关键。

---

### 1.5 元编程多智能体协作

| 属性 | 详情 |
|-----|------|
| **发布机构** | 上海人工智能实验室 |
| **论文标题** | MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework |
| **核心主题** | 基于元编程的多智能体协作框架，引入标准化 SOP 流程规范智能体行为，解决多智能体协作中的信息不一致与循环问题 |
| **发布时间** | 2023 年 8 月 |
| **访问链接** | [arXiv:2308.00352](https://arxiv.org/abs/2308.00352) / [GitHub](https://github.com/geekan/MetaGPT) |

**关键洞察**: 将软件工程的 SOP（标准操作流程）引入多智能体系统，通过角色分工和结构化输出显著提升协作效率。

---

### 1.6 基础智能体权威综述

| 属性 | 详情 |
|-----|------|
| **发布机构** | 蒙特利尔大学、微软亚洲研究院、谷歌 DeepMind 等 19 家机构 |
| **论文标题** | Advances and Challenges in Foundation Agents |
| **核心主题** | 基础智能体领域权威综述，整合全球 19 家机构的研究成果，提出智能体系统的完整技术框架与未来发展蓝图 |
| **发布时间** | 2025 年 3 月 |
| **访问链接** | [arXiv:2403.02164](https://arxiv.org/abs/2403.02164) |

**关键洞察**: 系统梳理了基础智能体的感知、推理、行动、学习四大能力模块，是进入该领域的必读文献。

---

### 1.7 智能体系统扩展规律

| 属性 | 详情 |
|-----|------|
| **发布机构** | Google DeepMind |
| **论文标题** | Towards a Science of Scaling Agent Systems |
| **核心主题** | 系统研究智能体系统的扩展规律与架构设计原则，对比不同多智能体拓扑结构的性能特征，为大规模智能体系统设计提供理论指导 |
| **发布时间** | 2025 年 12 月 |
| **访问链接** | [arXiv:2512.02095](https://arxiv.org/abs/2512.02095) |

**关键洞察**: 智能体系统的性能扩展并非线性，不同拓扑结构（链式、树形、图状）在不同任务类型上表现各异。

---

### 1.8 微软统一智能体框架

| 属性 | 详情 |
|-----|------|
| **发布机构** | Microsoft |
| **论文标题** | Microsoft Agent Framework: Unified Agent Development Toolkit |
| **核心主题** | 统一 Semantic Kernel 与 AutoGen 的下一代智能体开发框架，提供企业级状态管理、可观测性与全流程部署支持 |
| **发布时间** | 2025 年 10 月 |
| **访问链接** | [Microsoft Learn](https://learn.microsoft.com/en-us/ai/playbook/technology-guidance/generative-ai/agent-framework/) |

**关键洞察**: 企业级智能体框架需要整合多种技术路线，提供统一的开发体验和完整的运维支持。

---

## 二、Context Engineering 核心文献

### 2.1 上下文工程权威综述

| 属性 | 详情 |
|-----|------|
| **发布机构** | 中科院计算所、北京大学、清华大学 |
| **论文标题** | A Survey of Context Engineering for Large Language Models |
| **核心主题** | 上下文工程领域最全面的权威综述，系统分析 1400 + 篇相关论文，首次提出 "基础组件 - 系统实现" 两层分类框架，完整定义了上下文工程的学科体系 |
| **发布时间** | 2025 年 7 月 |
| **访问链接** | [arXiv:2507.13334](https://arxiv.org/abs/2507.13334) |

**关键洞察**: 上下文工程已从简单的提示词设计发展为包含采集、存储、管理、使用的完整系统工程。

---

### 2.2 主动式上下文工程

| 属性 | 详情 |
|-----|------|
| **发布机构** | 斯坦福大学、UC 伯克利、SambaNova |
| **论文标题** | Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models |
| **核心主题** | 提出 ACE（主动式上下文工程）框架，将上下文视为可进化的操作手册，通过 "生成 - 反思 - 整合" 的模块化流程实现模型自进化，无需微调即可显著提升任务性能 |
| **发布时间** | 2025 年 10 月 |
| **访问链接** | [arXiv:2510.04618](https://arxiv.org/abs/2510.04618) |

**关键洞察**: 上下文不应是静态的，而应通过智能体自主迭代优化，实现上下文驱动的模型能力提升。

---

### 2.3 上下文工程 2.0 范式

| 属性 | 详情 |
|-----|------|
| **发布机构** | 上海交通大学 GAIR 研究院 |
| **论文标题** | Context Engineering 2.0: The Context of Context Engineering |
| **核心主题** | 系统化定义上下文工程 2.0 范式，完成从 "静态提示词" 到 "动态情境系统" 的升级，归纳了上下文采集、存储、管理、使用四大核心环节的设计原则 |
| **发布时间** | 2025 年 10 月 |
| **访问链接** | [arXiv:2510.26493](https://arxiv.org/abs/2510.26493) |

**关键洞察**: 上下文工程 2.0 强调情境的动态性和系统性，需要建立完整的上下文生命周期管理体系。

---

### 2.4 智能体场景上下文工程

| 属性 | 详情 |
|-----|------|
| **发布机构** | Anthropic |
| **论文标题** | Efficient Context Engineering for AI Agents |
| **核心主题** | 面向智能体场景的上下文工程工程化方法论，提出系统提示设计、工具效率优化、示例质量控制三大核心原则，针对性解决长任务中的上下文腐烂（Context Rot）问题 |
| **发布时间** | 2025 年 11 月 |
| **访问链接** | [Anthropic Blog](https://www.anthropic.com/engineering/context-engineering-for-agents) |

**关键洞察**: 长任务中的上下文腐烂是智能体系统的核心挑战，需要通过主动压缩和关键信息提取来维护上下文质量。

---

### 2.5 符号调优技术

| 属性 | 详情 |
|-----|------|
| **发布机构** | Google Research |
| **论文标题** | Symbol Tuning: Improving In-Context Learning in Language Models |
| **核心主题** | 提出符号调优技术，通过将自然语言标签替换为任意符号，提升模型在未见上下文中的任务学习能力，在算法推理任务上实现最高 18.2% 的性能提升 |
| **发布时间** | 2023 年 5 月 |
| **访问链接** | [arXiv:2305.08298](https://arxiv.org/abs/2305.08298) |

**关键洞察**: 减少上下文中的语义偏见，使用抽象符号可以迫使模型更关注任务结构而非表面语义。

---

### 2.6 上下文优化方法

| 属性 | 详情 |
|-----|------|
| **发布机构** | 华盛顿大学、艾伦人工智能研究所 |
| **论文标题** | Context Optimization (CoOp) for Vision-Language Models |
| **核心主题** | 提出上下文优化（CoOp）方法，通过学习连续向量自动生成最优上下文，消除了手动提示调整的瓶颈，是自动化上下文工程的奠基性工作 |
| **发布时间** | 2021 年 9 月 |
| **访问链接** | [arXiv:2109.01134](https://arxiv.org/abs/2109.01134) |

**关键洞察**: 自动化的上下文优化可以显著减少人工调优成本，是上下文工程走向工程化的重要里程碑。

---

## 三、Harness Engineering 核心文献

### 3.1 Harness Engineering 范式定义

| 属性 | 详情 |
|-----|------|
| **发布机构** | OpenAI |
| **论文标题** | Harness Engineering: Leveraging Codex in an Agent-First World |
| **核心主题** | 正式提出 Harness Engineering（驾驭工程）范式，定义 AI 时代的新型软件工程方法论，提出 "Agent = Model + Harness" 核心公式，系统阐述了智能体外围系统的设计原则 |
| **发布时间** | 2026 年 2 月 |
| **访问链接** | [OpenAI Blog](https://openai.com/index/harness-engineering/) |

**关键洞察**: 智能体的能力不仅取决于模型本身，更取决于外围 Harness 系统的设计质量，Harness 是模型能力的放大器。

---

### 3.2 长时间运行智能体的 Harness 设计

| 属性 | 详情 |
|-----|------|
| **发布机构** | Anthropic |
| **论文标题** | Effective Harnesses for Long-Running Agents |
| **核心主题** | 面向长时间运行智能体的 Harness 设计工程实践，提出状态管理器、工具控制器、内存模块、调度器四大核心架构组件，给出了企业级 Harness 系统的落地指南 |
| **发布时间** | 2025 年 11 月 |
| **访问链接** | [Anthropic Blog](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) |

**关键洞察**: 长时间运行的智能体需要完善的 Harness 系统来管理状态、内存和工具调用，四大组件是构建健壮智能体的基础。

---

### 3.3 Deep Agent Harness 优化实践

| 属性 | 详情 |
|-----|------|
| **发布机构** | LangChain |
| **论文标题** | Improving Deep Agents with Harness Engineering |
| **核心主题** | 基于 DeepAgent 的 Harness 工程优化实践，针对性解决 Supervisor 架构的三大性能瓶颈，通过工具命名优化、上下文管理、错误处理增强，实现智能体性能近 50% 的提升 |
| **发布时间** | 2026 年 2 月 |
| **访问链接** | [LangChain Docs](https://python.langchain.com/docs/concepts/agents/deep_agents/) |

**关键洞察**: Harness 工程的细节优化（如工具命名、错误处理）可以带来显著的性能提升，是工程化落地的关键。


---

### 3.4 自然语言单元测试

| 属性 | 详情 |
|-----|------|
| **发布机构** | 斯坦福大学、CMU |
| **论文标题** | LMUNIT: Natural Language Unit Testing for LLMs |
| **核心主题** | 提出面向 LLM 的自然语言单元测试范式，将模型响应质量分解为明确的可测试标准，为 Harness 系统构建了完整的自动化评估框架 |
| **发布时间** | 2025 年 10 月 |
| **访问链接** | [arXiv:2510.03125](https://arxiv.org/abs/2510.03125) |

**关键洞察**: 为 LLM 输出建立可测试的质量标准是实现可靠 Harness 系统的前提，自然语言单元测试是有效的评估手段。

---

### 3.5 智能体综合评估框架

| 属性 | 详情 |
|-----|------|
| **发布机构** | 清华大学 THUDM 团队 |
| **论文标题** | AgentBench: Evaluating LLMs as Agents |
| **核心主题** | 首个多环境 LLM 智能体综合评估框架，构建了 Harness 系统的多维度评估体系，覆盖操作系统、数据库、Web 浏览等 8 个真实场景的智能体能力测试 |
| **发布时间** | 2023 年 8 月 |
| **访问链接** | [arXiv:2308.03688](https://arxiv.org/abs/2308.03688) / [GitHub](https://github.com/THUDM/AgentBench) |

**关键洞察**: 系统化的评估框架是 Harness 工程的重要组成部分，多场景测试能全面反映智能体的真实能力。

---

## 四、研究趋势总结

### 4.1 三大核心趋势

```
┌─────────────────────────────────────────────────────────────────┐
│                     Agent 技术演进趋势                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 从单智能体到多智能体协作                                      │
│     ├── MetaGPT: SOP驱动的协作                                    │
│     ├── MoA: 分层混合架构                                         │
│     └── AgentScope: 企业级多智能体框架                            │
│                                                                 │
│  2. 从静态提示到动态上下文工程                                     │
│     ├── Context Engineering 2.0: 系统化上下文管理                  │
│     ├── ACE: 主动式上下文进化                                     │
│     └── 上下文腐烂治理: 长任务优化                                 │
│                                                                 │
│  3. 从模型中心到 Harness 中心                                     │
│     ├── Harness Engineering 范式定义                              │
│     ├── Agent = Model + Harness 公式                              │
│     └── 四大组件: 状态/工具/内存/调度                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 对 GoldMiner 的启示

| 研究方向 | GoldMiner 应用建议 |
|---------|-------------------|
| **多智能体协作** | 考虑将 SQL 生成、数据分析、报告生成拆分为独立智能体 |
| **上下文工程** | 建立表结构、指标定义、业务背景的结构化上下文管理 |
| **Harness 设计** | 完善状态管理、工具调用控制、会话记忆、任务调度四大模块 |
| **评估体系** | 建立 SQL 正确性、分析质量、报告完整性的自动化评估 |

### 4.3 推荐阅读顺序

**入门路径**:
1. [Advances and Challenges in Foundation Agents](#16-基础智能体权威综述) - 建立整体认知
2. [A Survey of Context Engineering](#21-上下文工程权威综述) - 理解上下文工程全貌
3. [Harness Engineering: Leveraging Codex](#31-harness-engineering-范式定义) - 掌握 Harness 范式

**进阶路径**:
4. [Agentic Context Engineering](#22-主动式上下文工程) - 动态上下文优化
5. [Effective Harnesses for Long-Running Agents](#32-长时间运行智能体的-harness-设计) - 企业级 Harness 设计
6. [Towards a Science of Scaling Agent Systems](#17-智能体系统扩展规律) - 规模化设计原则

---

**文档维护记录**

| 版本 | 日期 | 修改人 | 说明 |
|-----|------|-------|------|
| v1.0 | 2026-03-24 | AI Assistant | 初始整理版本 |

