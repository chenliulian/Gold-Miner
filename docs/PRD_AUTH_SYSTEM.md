# GoldMiner 用户认证与数据隔离系统 - 产品需求设计文档

**版本**: v1.0  
**日期**: 2026-03-24  
**状态**: 设计阶段  

---

## 1. 文档概述

### 1.1 背景
GoldMiner 目前是一个单用户系统，所有用户共享同一套会话历史、长期记忆和学习记录。随着产品推广，需要支持多用户场景，每个用户应有独立的数据空间，同时保持便捷的登录体验。

### 1.2 目标
- 实现基于飞书SSO的用户注册/登录系统
- 兼容企业员工系统API，支持组织架构同步
- 实现用户数据完全隔离（会话、记忆、学习记录）
- 保持业务知识库全局共享

### 1.3 范围
- 用户认证模块（注册、登录、登出、会话管理）
- 飞书SSO集成（扫码登录）
- 企业员工系统API对接
- 多用户数据隔离架构
- 权限控制（RBAC）

---

## 2. 用户故事

### 2.1 普通用户
- 作为**企业员工**，我希望**用飞书扫码快速登录**，以便**无需记住额外密码**
- 作为**分析师**，我希望**我的对话历史只有我能看到**，以便**保护数据隐私**
- 作为**团队成员**，我希望**系统记住我常用的表结构**，以便**提高查询效率**

### 2.2 管理员
- 作为**系统管理员**，我希望**同步企业组织架构**，以便**自动管理用户权限**
- 作为**安全负责人**，我希望**查看登录审计日志**，以便**追踪异常访问**

---

## 3. 系统架构

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              用户端                                       │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────┐   │
│  │   Web 浏览器  │     │  飞书 APP   │     │    飞书扫一扫 (二维码)    │   │
│  └──────┬──────┘     └──────┬──────┘     └───────────┬─────────────┘   │
└─────────┼───────────────────┼────────────────────────┼─────────────────┘
          │                   │                        │
          ▼                   ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           GoldMiner 后端服务                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        Flask App                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │  /auth/*    │  │  /api/*     │  │    /feishu/webhook      │  │   │
│  │  │  认证接口    │  │  业务API    │  │    飞书事件回调          │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │   │
│  │         └─────────────────┴─────────────────────┘                │   │
│  │                              │                                   │   │
│  │                    ┌─────────┴─────────┐                        │   │
│  │                    ▼                   ▼                        │   │
│  │           ┌─────────────┐    ┌─────────────────┐               │   │
│  │           │  AuthService │    │  FeishuAuth     │               │   │
│  │           │  认证服务    │◄──►│  飞书SSO集成    │               │   │
│  │           └──────┬──────┘    └─────────────────┘               │   │
│  │                  │                                              │   │
│  │         ┌────────┴────────┐                                     │   │
│  │         ▼                 ▼                                     │   │
│  │  ┌─────────────┐   ┌─────────────┐                             │   │
│  │  │  UserModel  │   │  Session    │                             │   │
│  │  │  用户数据    │   │  会话管理    │                             │   │
│  │  └─────────────┘   └─────────────┘                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         外部系统集成                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐     │
│  │  飞书开放平台    │  │  企业员工系统API │  │   Redis/内存存储      │     │
│  │  (SSO/扫码)     │  │  (组织架构同步)  │  │   (Session/Token)   │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 数据隔离架构

```
/Users/shmichenliulian/GoldMiner/
├── data/                                    # 用户数据根目录
│   ├── users.json                           # 用户索引
│   │
│   ├── user_{user_id_1}/                    # 用户1的数据目录
│   │   ├── profile.json                     # 用户基本信息
│   │   ├── sessions/                        # 会话历史
│   │   ├── memory/                          # 长期记忆
│   │   ├── learnings/                       # 个人学习记录
│   │   └── reports/                         # 个人报告
│   │
│   ├── user_{user_id_2}/                    # 用户2的数据目录
│   │   └── ...
│   │
│   └── shared/                              # 共享数据
│       ├── global_learnings/                # 全局学习记录
│       └── common_knowledge/                # 公共知识库
│
├── skills/                                  # 技能目录（全局共享）
└── ui/                                      # Web界面
```

---

## 4. 功能需求

### 4.1 飞书SSO登录

#### 4.1.1 扫码登录流程

```
┌─────────┐                              ┌─────────────┐                              ┌─────────────┐
│  用户   │                              │  GoldMiner  │                              │  飞书服务器  │
└────┬────┘                              └──────┬──────┘                              └──────┬──────┘
   │                                            │                                            │
   │  1. 访问 /login                             │                                            │
   │ ─────────────────────────────────────────► │                                            │
   │                                            │                                            │
   │                                            │  2. 生成二维码 (调用飞书API)                 │
   │                                            │ ─────────────────────────────────────────► │
   │                                            │                                            │
   │                                            │  3. 返回二维码 URL + 临时 state             │
   │                                            │ ◄───────────────────────────────────────── │
   │                                            │                                            │
   │  4. 展示二维码                              │                                            │
   │ ◄───────────────────────────────────────── │                                            │
   │                                            │                                            │
   │  5. 飞书APP扫码授权                          │                                            │
   │ ─────────────────────────────────────────────────────────────────────────────────────► │
   │                                            │                                            │
   │                                            │  6. 飞书回调 /auth/feishu/callback          │
   │                                            │ ◄───────────────────────────────────────── │
   │                                            │                                            │
   │                                            │  7. 用code换access_token                   │
   │                                            │ ─────────────────────────────────────────► │
   │                                            │                                            │
   │                                            │  8. 获取用户信息                            │
   │                                            │ ─────────────────────────────────────────► │
   │                                            │                                            │
   │                                            │  9. 查询/创建本地用户                       │
   │                                            │  10. 生成JWT Session                       │
   │                                            │                                            │
   │  11. 登录成功跳转                            │                                            │
   │ ◄───────────────────────────────────────── │                                            │
   │                                            │                                            │
```

#### 4.1.2 接口定义

| 接口 | 方法 | 描述 | 请求参数 | 响应 |
|-----|------|------|---------|------|
| `/auth/login` | GET | 登录页面 | - | HTML页面（含二维码） |
| `/auth/feishu/qrcode` | GET | 获取二维码 | - | `{qr_url, state}` |
| `/auth/feishu/callback` | GET | 飞书回调 | `code`, `state` | 重定向到首页 |
| `/auth/feishu/poll` | GET | 轮询登录状态 | `state` | `{status, token?}` |
| `/auth/logout` | POST | 退出登录 | - | `{success}` |
| `/auth/me` | GET | 当前用户信息 | Header: Authorization | `{user_id, name, ...}` |
| `/auth/refresh` | POST | 刷新Token | Header: Authorization | `{token}` |

### 4.2 企业员工系统集成

#### 4.2.1 集成方式

| 场景 | 方案 | 说明 |
|-----|------|------|
| 企业有标准API | 实时查询 | 登录时调用企业API验证员工身份 |
| 企业有飞书集成 | 飞书获取 | 通过飞书API获取部门/员工信息 |
| 企业无API | 定期导入 | 管理员手动导入员工CSV |

#### 4.2.2 数据同步字段

```python
{
    "employee_id": "E12345",           # 员工工号
    "name": "张三",                    # 姓名
    "email": "zhangsan@company.com",   # 邮箱
    "department_id": "D001",           # 部门ID
    "department_name": "数据部",        # 部门名称
    "job_title": "高级分析师",          # 职位
    "manager_id": "E12300",            # 直属领导
    "entry_date": "2023-01-15",        # 入职日期
    "status": "active"                 # 在职状态
}
```

### 4.3 用户数据隔离

#### 4.3.1 隔离策略

| 数据类型 | 隔离级别 | 存储位置 | 说明 |
|---------|---------|---------|------|
| 会话历史 | 完全隔离 | `data/user_{id}/sessions/` | 每个用户独立的对话记录 |
| 长期记忆 | 完全隔离 | `data/user_{id}/memory/` | 用户要求记住的内容 |
| 学习记录 | 完全隔离 | `data/user_{id}/learnings/` | 个人学习积累 |
| 分析报告 | 完全隔离 | `data/user_{id}/reports/` | 生成的报告 |
| 用户配置 | 完全隔离 | `data/user_{id}/profile.json` | 个人设置 |
| 业务知识库 | 全局共享 | `knowledge/` | 所有用户只读访问 |
| 技能(Skill) | 全局共享 | `skills/` | 所有用户共享 |

#### 4.3.2 用户目录结构

```
data/user_{user_id}/
├── profile.json              # 用户基本信息
├── sessions/                 # 会话历史
│   ├── session_20240324_101530_123456.json
│   └── session_20240324_102045_789012.json
├── memory/                   # 长期记忆
│   ├── state.json           # 记忆状态
│   └── summary.md           # 记忆摘要
├── learnings/                # 个人学习记录
│   └── learnings.md
└── reports/                  # 个人报告
    └── report_20240324_103000.md
```

### 4.4 权限控制（RBAC）

#### 4.4.1 角色定义

| 角色 | 权限 | 适用人群 |
|-----|------|---------|
| **admin** | 所有权限 | 系统管理员 |
| **analyst** | chat:query, export:report, view:dashboard | 数据分析师 |
| **viewer** | view:dashboard | 只读用户 |

#### 4.4.2 权限列表

```python
PERMISSIONS = {
    # 对话相关
    "chat:query": "执行数据查询对话",
    "chat:export": "导出对话内容",
    
    # 报告相关
    "export:report": "导出分析报告",
    "view:dashboard": "查看仪表板",
    
    # 管理相关
    "admin:user": "管理用户",
    "admin:sync": "同步企业数据",
    "admin:config": "系统配置",
}
```

---

## 5. 数据模型

### 5.1 用户模型

```python
class User:
    """用户模型"""
    
    # 主键
    id: str                        # UUID
    
    # 飞书信息
    feishu_open_id: str           # 飞书用户唯一标识
    feishu_union_id: str          # 飞书union_id
    feishu_user_id: str           # 飞书user_id
    
    # 基本信息
    name: str                     # 用户姓名
    email: str                    # 邮箱
    mobile: str                   # 手机号（脱敏）
    avatar: str                   # 头像URL
    
    # 企业信息
    employee_id: str              # 员工工号
    department_id: str            # 部门ID
    department_name: str          # 部门名称
    job_title: str                # 职位
    
    # 权限控制
    role: str                     # 角色: admin/analyst/viewer
    is_active: bool               # 是否启用
    permissions: List[str]        # 权限列表
    
    # 时间戳
    created_at: datetime          # 首次注册时间
    updated_at: datetime          # 信息更新时间
    last_login_at: datetime       # 最后登录时间
```

### 5.2 会话模型

```python
class SessionState:
    """单次对话的完整状态"""
    
    session_id: str               # 会话ID
    user_id: str                  # 所属用户ID
    start_time: str               # 开始时间
    end_time: Optional[str]       # 结束时间
    title: str                    # 对话标题
    steps: List[Dict]             # 对话步骤
    metadata: Dict                # 元数据
```

### 5.3 登录日志模型

```python
class LoginLog:
    """登录审计日志"""
    
    id: str
    user_id: str
    login_type: str               # feishu_qr / feishu_auto
    ip_address: str
    user_agent: str
    status: str                   # success / failed
    error_msg: str                # 失败原因
    created_at: datetime
```

---

## 6. 接口详细设计

### 6.1 认证接口

#### POST /auth/feishu/callback
飞书授权回调

**请求参数**:
```json
{
    "code": "xxx",
    "state": "yyy"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "token": "jwt_token",
        "expires_in": 28800,
        "user": {
            "id": "user_uuid",
            "name": "张三",
            "email": "zhangsan@company.com",
            "role": "analyst"
        }
    }
}
```

#### GET /auth/me
获取当前用户信息

**请求头**:
```
Authorization: Bearer {jwt_token}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "id": "user_uuid",
        "name": "张三",
        "email": "zhangsan@company.com",
        "avatar": "https://...",
        "department": "数据部",
        "role": "analyst",
        "permissions": ["chat:query", "export:report"],
        "created_at": "2024-01-15T10:30:00Z",
        "last_login_at": "2024-03-24T08:15:00Z"
    }
}
```

### 6.2 会话接口

#### GET /api/v2/sessions
列出当前用户的所有会话

**响应**:
```json
{
    "success": true,
    "data": [
        {
            "session_id": "session_20240324_101530_123456",
            "title": "Q1销售数据分析",
            "start_time": "2024-03-24T10:15:30Z",
            "end_time": "2024-03-24T10:45:20Z",
            "step_count": 12
        }
    ]
}
```

#### POST /api/v2/sessions/{id}/switch
切换到指定会话

**响应**:
```json
{
    "success": true,
    "data": {
        "session_id": "session_20240324_101530_123456",
        "steps": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
}
```

### 6.3 记忆接口

#### GET /api/v2/memory
获取当前用户的长期记忆

**响应**:
```json
{
    "success": true,
    "data": {
        "summary": "用户主要分析销售数据...",
        "table_schemas": {
            "sales_order": ["order_id", "amount", "created_at"]
        },
        "metric_definitions": {
            "GMV": "成交总额"
        },
        "business_background": [
            "关注Q1季度销售趋势"
        ]
    }
}
```

---

## 7. 安全设计

### 7.1 认证安全

| 措施 | 说明 |
|-----|------|
| JWT Token | 使用HS256算法，有效期8小时 |
| Refresh Token | 有效期7天，用于刷新Access Token |
| State参数 | 防止CSRF攻击 |
| HTTPS | 所有接口强制HTTPS |

### 7.2 数据安全

| 措施 | 说明 |
|-----|------|
| 数据隔离 | 每个用户独立目录，禁止跨用户访问 |
| 敏感信息脱敏 | 手机号、邮箱等敏感信息脱敏存储 |
| 审计日志 | 记录所有登录/敏感操作 |

### 7.3 配置项

```ini
# JWT配置
JWT_SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 飞书配置
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_REDIRECT_URI=https://your-domain.com/auth/feishu/callback

# 企业API配置
ENTERPRISE_API_BASE_URL=https://hr-api.company.com
ENTERPRISE_API_KEY=xxxxxxxxxxxx
ENTERPRISE_SYNC_INTERVAL=3600
```

---

## 8. 实施计划

### Phase 1: 基础飞书SSO (2周)
- [ ] 飞书自建应用配置
- [ ] 扫码登录流程实现
- [ ] JWT Token认证
- [ ] 基础用户模型

### Phase 2: 数据隔离 (2周)
- [ ] 用户目录结构实现
- [ ] UserSessionStore改造
- [ ] UserMemoryStore改造
- [ ] UserAgentPool改造

### Phase 3: 企业集成 (1周)
- [ ] 企业员工系统API对接
- [ ] 组织架构同步
- [ ] 权限映射配置

### Phase 4: 增强功能 (1周)
- [ ] 登录审计日志
- [ ] 会话管理（踢人/强制下线）
- [ ] 管理后台

---

## 9. 风险评估

| 风险 | 影响 | 概率 | 应对措施 |
|-----|------|------|---------|
| 飞书API变更 | 高 | 低 | 封装飞书API调用层，便于适配 |
| 企业API不稳定 | 中 | 中 | 实现降级策略，允许本地缓存 |
| 数据迁移问题 | 高 | 低 | 保留现有数据作为"默认用户" |
| 性能瓶颈 | 中 | 低 | 使用AgentPool复用，Redis缓存 |

---

## 10. 附录

### 10.1 术语表

| 术语 | 说明 |
|-----|------|
| SSO | Single Sign-On，单点登录 |
| JWT | JSON Web Token |
| RBAC | Role-Based Access Control，基于角色的访问控制 |
| CSRF | Cross-Site Request Forgery，跨站请求伪造 |

### 10.2 参考文档

- [飞书开放平台 - 扫码登录](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/authen-v1/login-overview)
- [JWT标准](https://tools.ietf.org/html/rfc7519)

---

**文档维护记录**

| 版本 | 日期 | 修改人 | 说明 |
|-----|------|-------|------|
| v1.0 | 2026-03-24 | AI Assistant | 初始版本 |
