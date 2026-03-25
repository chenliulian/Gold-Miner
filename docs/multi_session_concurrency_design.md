# GoldMiner 多会话并行处理实现方案

## 1. 问题分析

### 1.1 当前架构限制

#### 前端问题
- `isProcessing` 是全局变量，控制整个页面的输入状态
- 当一个会话在运行时，所有会话的输入框都会被禁用
- 用户无法在其他会话中输入问题

#### 后端问题
- `get_agent()` 返回全局单例 `AGENT`
- 所有会话共享同一个 `SqlAgent` 实例
- `SqlAgent` 内部有状态 (`AgentState`)，同一时间只能处理一个请求

### 1.2 已有基础设施
- **Agent Pool**: 已存在 `AgentPool` 类，支持多 Agent 实例管理
- **Session Store**: 每个 Agent 有自己的 `SessionStore`，会话数据独立存储
- **会话隔离**: 会话数据按 `session_id` 存储在独立文件中

---

## 2. 设计方案

### 2.1 核心设计原则

1. **会话级隔离**: 每个会话拥有独立的处理状态
2. **Agent 复用**: 使用 Agent Pool 管理多个 Agent 实例
3. **向后兼容**: 保持现有 API 接口不变
4. **资源控制**: 限制并发数量，防止资源耗尽

### 2.2 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         前端 (Browser)                        │
├─────────────────────────────────────────────────────────────┤
│  会话A (运行中)        会话B (空闲)        会话C (运行中)       │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐       │
│  │输入框 禁用│        │输入框 可用│        │输入框 禁用│       │
│  │显示 X 按钮│        │显示发送按钮│        │显示 X 按钮│       │
│  └──────────┘        └──────────┘        └──────────┘       │
│                                                             │
│  sessionStates: {                                           │
│    "session_a": { isProcessing: true },                    │
│    "session_b": { isProcessing: false },                   │
│    "session_c": { isProcessing: true }                     │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端 (Flask Server)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Agent Pool (max=10)                 │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │   │
│  │  │ Agent 1 │  │ Agent 2 │  │ Agent 3 │  │  ...    │ │   │
│  │  │(会话A)  │  │(会话B)  │  │(会话C)  │  │         │ │   │
│  │  │ in_use  │  │  idle   │  │ in_use  │  │         │ │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  请求处理流程:                                               │
│  1. /chat (session_id=A) → acquire() → Agent 1             │
│  2. /chat (session_id=B) → acquire() → Agent 2             │
│  3. /chat (session_id=C) → acquire() → Agent 3             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 详细实现方案

### 3.1 前端改造

#### 3.1.1 状态管理改造

**当前代码 (ui/templates/index.html)**:
```javascript
// 全局状态 - 问题所在
let isProcessing = false;
```

**改造后代码**:
```javascript
// 按会话维护处理状态
const sessionStates = new Map();

// 获取当前会话的处理状态
function isCurrentSessionProcessing() {
    return sessionStates.get(currentSessionId)?.isProcessing || false;
}

// 设置当前会话的处理状态
function setSessionProcessing(sessionId, processing) {
    sessionStates.set(sessionId, { 
        isProcessing: processing,
        startTime: processing ? Date.now() : null,
        abortController: processing ? new AbortController() : null
    });
    if (sessionId === currentSessionId) {
        updateSendButton();
    }
}
```

#### 3.1.2 发送消息函数改造

**当前代码**:
```javascript
async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    
    if (!message || isProcessing) return;  // 全局检查
    
    // ...
    isProcessing = true;  // 全局设置
    updateSendButton();
    // ...
}
```

**改造后代码**:
```javascript
async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    
    // 按当前会话检查
    if (!message || isCurrentSessionProcessing()) return;
    
    const activeSessionId = currentSessionId;
    
    // ...
    setSessionProcessing(activeSessionId, true);
    
    try {
        const state = sessionStates.get(activeSessionId);
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message, 
                stream: true,
                session_id: activeSessionId  // 传递会话ID
            }),
            signal: state.abortController.signal  // 支持取消
        });
        // ...
    } finally {
        setSessionProcessing(activeSessionId, false);
    }
}
```

#### 3.1.3 按钮状态更新改造

**当前代码**:
```javascript
function updateSendButton() {
    const sendBtn = document.getElementById('send-btn');
    const cancelBtn = document.getElementById('cancel-btn');

    if (isProcessing) {  // 全局判断
        sendBtn.style.display = 'none';
        cancelBtn.style.display = 'flex';
    } else {
        sendBtn.style.display = 'flex';
        cancelBtn.style.display = 'none';
    }
}
```

**改造后代码**:
```javascript
function updateSendButton() {
    const sendBtn = document.getElementById('send-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    
    // 按当前会话判断
    const processing = isCurrentSessionProcessing();

    if (processing) {
        sendBtn.style.display = 'none';
        cancelBtn.style.display = 'flex';
        cancelBtn.onclick = () => cancelMessage(currentSessionId);
    } else {
        sendBtn.style.display = 'flex';
        cancelBtn.style.display = 'none';
    }
}
```

#### 3.1.4 会话切换处理

**新增代码**:
```javascript
// 切换会话时更新UI状态
async function switchSession(sessionId) {
    currentSessionId = sessionId;
    
    // 加载会话历史
    await loadSessionHistory(sessionId);
    
    // 更新输入框状态
    updateSendButton();
    
    // 如果该会话正在处理中，显示处理状态
    const state = sessionStates.get(sessionId);
    if (state?.isProcessing) {
        showProcessingIndicator(sessionId);
    }
}

// 显示处理中指示器
function showProcessingIndicator(sessionId) {
    // 显示"该会话正在处理中"的提示
    const statusEl = document.getElementById('session-status');
    if (statusEl) {
        statusEl.textContent = '处理中...';
        statusEl.style.display = 'block';
    }
}
```

---

### 3.2 后端改造

#### 3.2.1 修改 `/chat` 接口支持会话隔离

**当前代码 (ui/app.py)**:
```python
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    stream = data.get("stream", False)
    new_session = data.get("new_session", False)
    
    agent = get_agent()  # 全局单例
    
    # 如果需要开启新会话
    if new_session or agent.session.get_current_session_id() is None:
        session_title = user_message[:30] + "..."
        agent.start_new_session(title=session_title)
    
    # ... 处理逻辑
```

**改造后代码**:
```python
from gold_miner.services import get_agent_pool

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    stream = data.get("stream", False)
    session_id = data.get("session_id")  # 前端传递的会话ID
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    # 从 Agent Pool 获取 Agent
    agent_pool = get_agent_pool()
    
    try:
        # 为当前请求获取一个 Agent
        pooled_agent = agent_pool.acquire(session_id=session_id)
        agent = pooled_agent.agent
        
        # 加载指定会话上下文
        if session_id:
            agent.session.load_session(session_id)
        else:
            # 创建新会话
            session_title = user_message[:30] + "..."
            session_id = agent.start_new_session(title=session_title)
        
        def generate():
            try:
                # ... 原有处理逻辑
                yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
                # ...
            finally:
                # 释放 Agent 回连接池
                agent_pool.release(pooled_agent)
        
        if stream:
            return Response(generate(), mimetype='text/event-stream')
        else:
            # 非流式处理
            try:
                # ... 处理逻辑
                return jsonify({
                    "success": True,
                    "response": response_text,
                    "session_id": session_id,
                })
            finally:
                agent_pool.release(pooled_agent)
                
    except RuntimeError as e:
        if "Agent pool exhausted" in str(e):
            return jsonify({
                "error": "系统繁忙，请稍后再试",
                "retry_after": 5
            }), 503
        raise
```

#### 3.2.2 修改 `/interrupt` 接口支持按会话取消

**当前代码**:
```python
@app.route("/interrupt", methods=["POST"])
def interrupt():
    """中断当前 Agent 的执行"""
    agent = get_agent()
    if hasattr(agent, 'interrupt'):
        agent.interrupt()
    return jsonify({"success": True})
```

**改造后代码**:
```python
@app.route("/interrupt", methods=["POST"])
def interrupt():
    """中断指定会话的 Agent 执行"""
    data = request.json or {}
    session_id = data.get("session_id")
    
    agent_pool = get_agent_pool()
    
    # 查找正在处理该会话的 Agent
    with agent_pool._lock:
        for pooled_agent in agent_pool._pool:
            if pooled_agent.session_id == session_id and pooled_agent.in_use:
                if hasattr(pooled_agent.agent, 'interrupt'):
                    pooled_agent.agent.interrupt()
                return jsonify({"success": True})
    
    return jsonify({"success": False, "error": "Session not found or not processing"}), 404
```

#### 3.2.3 新增 Agent Pool 状态查询接口

```python
@app.route("/agent_pool/stats", methods=["GET"])
def get_agent_pool_stats():
    """获取 Agent Pool 状态"""
    agent_pool = get_agent_pool()
    return jsonify({
        "success": True,
        "stats": agent_pool.get_stats()
    })
```

#### 3.2.4 修改会话相关接口

**`/sessions/<session_id>` GET 接口**:
```python
@app.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
    """获取特定会话的详情 - 不需要占用 Agent"""
    # 直接读取会话文件，不占用 Agent
    sessions_dir = get_agent().session.sessions_dir
    session_path = os.path.join(sessions_dir, f"{session_id}.json")
    
    if not os.path.exists(session_path):
        return jsonify({"success": False, "error": "Session not found"}), 404
    
    with open(session_path, "r", encoding="utf-8") as f:
        session_data = json.load(f)
    
    return jsonify({
        "success": True,
        "session": session_data
    })
```

---

### 3.3 Agent Pool 增强

#### 3.3.1 新增按会话查找 Agent 功能

```python
# 在 AgentPool 类中添加

def get_agent_by_session(self, session_id: str) -> Optional[PooledAgent]:
    """获取正在处理指定会话的 Agent"""
    with self._lock:
        for pooled_agent in self._pool:
            if pooled_agent.session_id == session_id and pooled_agent.in_use:
                return pooled_agent
    return None

def is_session_processing(self, session_id: str) -> bool:
    """检查指定会话是否正在处理中"""
    return self.get_agent_by_session(session_id) is not None
```

#### 3.3.2 新增会话级取消支持

```python
def cancel_session(self, session_id: str) -> bool:
    """取消指定会话的处理"""
    pooled_agent = self.get_agent_by_session(session_id)
    if pooled_agent and hasattr(pooled_agent.agent, 'interrupt'):
        pooled_agent.agent.interrupt()
        return True
    return False
```

---

## 4. 数据流图

### 4.1 多会话并行处理流程

```
用户A (会话A)                    用户B (会话B)                    用户C (会话C)
   │                                │                                │
   │ 1. 发送问题                    │                                │
   │───────────────────────────────>│                                │
   │                                │                                │
   │                      2. 发送问题 (同时)                        │
   │<───────────────────────────────│───────────────────────────────>│
   │                                │                                │
   ▼                                ▼                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              前端 JavaScript                                 │
│  sessionStates = {                                                          │
│    "session_a": { isProcessing: true,  abortController: ctrl1 },           │
│    "session_b": { isProcessing: true,  abortController: ctrl2 },           │
│    "session_c": { isProcessing: false, abortController: null }             │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
   │                                │                                │
   │ 3. 请求 /chat (session_id=a)   │ 4. 请求 /chat (session_id=b)   │
   │───────────────────────────────>│───────────────────────────────>│
   │                                │                                │
   ▼                                ▼                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              后端 Flask                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Agent Pool                                  │   │
│  │  acquire(session_id="session_a") ──> Agent 1 (标记 in_use)          │   │
│  │  acquire(session_id="session_b") ──> Agent 2 (标记 in_use)          │   │
│  │                                                                     │   │
│  │  Agent 1 处理 session_a 的同时                                      │   │
│  │  Agent 2 处理 session_b (真正并行)                                   │   │
│  │                                                                     │   │
│  │  release(Agent 1) <── 处理完成 ── 标记 idle                         │   │
│  │  release(Agent 2) <── 处理完成 ── 标记 idle                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
   │                                │                                │
   │ 5. 返回结果                    │ 6. 返回结果                    │
   │<───────────────────────────────│<───────────────────────────────│
   │                                │                                │
   ▼                                ▼                                ▼
 显示结果                        显示结果                          等待输入
```

---

## 5. 关键代码文件变更清单

### 5.1 前端文件

| 文件 | 变更类型 | 变更内容 |
|------|----------|----------|
| `ui/templates/index.html` | 修改 | 1. 替换全局 `isProcessing` 为 `sessionStates` Map<br>2. 修改 `sendMessage()` 按会话处理<br>3. 修改 `updateSendButton()` 按当前会话判断<br>4. 修改 `cancelMessage()` 支持指定会话<br>5. 新增 `switchSession()` 处理会话切换 |

### 5.2 后端文件

| 文件 | 变更类型 | 变更内容 |
|------|----------|----------|
| `ui/app.py` | 修改 | 1. `/chat` 接口使用 Agent Pool<br>2. `/interrupt` 接口支持按会话取消<br>3. `/sessions/<id>` 直接读取文件不占用 Agent |
| `src/gold_miner/services/agent_pool.py` | 新增方法 | 1. `get_agent_by_session()`<br>2. `is_session_processing()`<br>3. `cancel_session()` |
| `src/gold_miner/agent.py` | 可选优化 | 考虑将 `AgentState` 与会话绑定而非 Agent 实例 |

---

## 6. 边界情况处理

### 6.1 Agent Pool 耗尽

```python
# 当所有 Agent 都在使用时
if len(self._pool) >= self.max_size and all(a.in_use for a in self._pool):
    return jsonify({
        "error": "系统繁忙，当前所有处理槽位已满",
        "retry_after": 5,
        "queue_position": estimate_queue_position()
    }), 503
```

### 6.2 会话切换时原会话完成

```javascript
// 处理异步完成的情况
function onSessionComplete(sessionId, result) {
    // 如果当前正在查看该会话，更新UI
    if (currentSessionId === sessionId) {
        displayResult(result);
        updateSendButton();
    } else {
        // 显示未读标记
        showUnreadIndicator(sessionId);
    }
}
```

### 6.3 重复提交保护

```javascript
// 防止同一会话重复提交
const pendingSessions = new Set();

async function sendMessage() {
    if (pendingSessions.has(currentSessionId)) {
        showToast("该会话正在处理中，请勿重复提交");
        return;
    }
    
    pendingSessions.add(currentSessionId);
    try {
        // ... 处理逻辑
    } finally {
        pendingSessions.delete(currentSessionId);
    }
}
```

---

## 7. 性能考虑

### 7.1 Agent Pool 大小配置

```python
# 根据服务器资源调整
AgentPool(
    min_size=2,      # 最小保持空闲的 Agent 数
    max_size=10,     # 最大并发数（根据 CPU/内存调整）
    max_idle_time=3600  # 空闲 Agent 回收时间
)
```

### 7.2 资源监控

```python
# 定期报告 Pool 状态
@app.route("/admin/metrics", methods=["GET"])
def get_metrics():
    agent_pool = get_agent_pool()
    stats = agent_pool.get_stats()
    
    return jsonify({
        "agent_pool": stats,
        "memory_usage": get_memory_usage(),
        "active_sessions": stats["in_use"],
        "queue_depth": get_queue_depth()
    })
```

---

## 8. 测试策略

### 8.1 单元测试

```python
# 测试 Agent Pool 的并发获取
def test_agent_pool_concurrent_acquire():
    pool = AgentPool(config, skills_dir, sessions_dir, max_size=3)
    
    # 同时获取 3 个 Agent
    agents = [pool.acquire(f"session_{i}") for i in range(3)]
    
    # 第 4 个应该失败
    with pytest.raises(RuntimeError):
        pool.acquire("session_4")
    
    # 释放后可以再次获取
    pool.release(agents[0])
    new_agent = pool.acquire("session_4")
    assert new_agent is not None
```

### 8.2 集成测试

```python
# 测试多会话并行处理
def test_multi_session_concurrent_processing(client):
    # 创建两个会话
    resp1 = client.post("/sessions/new", json={"title": "Test 1"})
    session1 = resp1.json["session_id"]
    
    resp2 = client.post("/sessions/new", json={"title": "Test 2"})
    session2 = resp2.json["session_id"]
    
    # 同时发送请求
    import threading
    results = {}
    
    def send_request(session_id, key):
        resp = client.post("/chat", json={
            "message": "测试查询",
            "session_id": session_id
        })
        results[key] = resp.status_code
    
    t1 = threading.Thread(target=send_request, args=(session1, "s1"))
    t2 = threading.Thread(target=send_request, args=(session2, "s2"))
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # 两个请求都应该成功
    assert results["s1"] == 200
    assert results["s2"] == 200
```

---

## 9. 部署注意事项

### 9.1 配置调整

```bash
# 根据服务器配置调整 Agent Pool 大小
export AGENT_POOL_MIN_SIZE=2
export AGENT_POOL_MAX_SIZE=10
export AGENT_POOL_MAX_IDLE_TIME=3600
```

### 9.2 监控告警

```yaml
# 监控指标
alerts:
  - name: agent_pool_exhausted
    condition: agent_pool_available == 0
    duration: 1m
    severity: warning
  
  - name: high_concurrent_sessions
    condition: agent_pool_in_use > 8
    duration: 5m
    severity: info
```

---

## 10. 总结

### 10.1 改造收益

1. **用户体验提升**: 用户可以在多个会话间自由切换，不受其他会话影响
2. **资源利用率**: 通过 Agent Pool 实现 Agent 复用，避免频繁创建销毁
3. **可扩展性**: 架构支持水平扩展，可通过增加服务器提升并发能力

### 10.2 改造成本

- **前端**: 约 100 行代码修改，主要是状态管理调整
- **后端**: 约 150 行代码修改，主要是接口适配
- **测试**: 需要新增并发测试用例

### 10.3 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 会话状态不一致 | 中 | 高 | 完善的单元测试和集成测试 |
| Agent Pool 泄漏 | 低 | 高 | 确保 finally 中调用 release |
| 内存溢出 | 低 | 高 | 限制 Pool 大小，监控内存使用 |

---

## 附录：完整代码示例

### A. 前端核心代码

```javascript
// ========== 会话状态管理 ==========
const sessionStates = new Map();

function getSessionState(sessionId) {
    if (!sessionStates.has(sessionId)) {
        sessionStates.set(sessionId, {
            isProcessing: false,
            startTime: null,
            abortController: null
        });
    }
    return sessionStates.get(sessionId);
}

function isCurrentSessionProcessing() {
    return currentSessionId ? getSessionState(currentSessionId).isProcessing : false;
}

function setSessionProcessing(sessionId, processing) {
    const state = getSessionState(sessionId);
    state.isProcessing = processing;
    state.startTime = processing ? Date.now() : null;
    state.abortController = processing ? new AbortController() : null;
    
    if (sessionId === currentSessionId) {
        updateSendButton();
    }
}

// ========== 发送消息 ==========
async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    const activeSessionId = currentSessionId;
    
    if (!message || getSessionState(activeSessionId).isProcessing) {
        return;
    }
    
    addMessage(message, 'user');
    input.value = '';
    input.style.height = 'auto';
    
    setSessionProcessing(activeSessionId, true);
    const logContainer = addLogMessage();
    
    try {
        const state = getSessionState(activeSessionId);
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message, 
                stream: true,
                session_id: activeSessionId
            }),
            signal: state.abortController.signal
        });
        
        // ... 处理响应
        
    } catch (error) {
        if (error.name === 'AbortError') {
            addMessage('已取消', 'assistant');
        } else {
            addMessage('错误: ' + error.message, 'assistant');
        }
    } finally {
        setSessionProcessing(activeSessionId, false);
    }
}

// ========== 取消消息 ==========
async function cancelMessage(sessionId) {
    const state = getSessionState(sessionId);
    if (state.abortController) {
        state.abortController.abort();
    }
    
    try {
        await fetch('/interrupt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
    } catch (error) {
        console.error('取消失败:', error);
    }
}

// ========== 更新按钮状态 ==========
function updateSendButton() {
    const sendBtn = document.getElementById('send-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const processing = isCurrentSessionProcessing();

    if (processing) {
        sendBtn.style.display = 'none';
        cancelBtn.style.display = 'flex';
    } else {
        sendBtn.style.display = 'flex';
        cancelBtn.style.display = 'none';
    }
}
```

### B. 后端核心代码

```python
# ========== /chat 接口 ==========
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    stream = data.get("stream", False)
    session_id = data.get("session_id")
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    agent_pool = get_agent_pool()
    
    try:
        pooled_agent = agent_pool.acquire(session_id=session_id)
        agent = pooled_agent.agent
        
        # 加载或创建会话
        if session_id:
            agent.session.load_session(session_id)
        else:
            session_title = user_message[:30] + "..."
            session_id = agent.start_new_session(title=session_title)
        
        def generate():
            try:
                yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
                # ... 原有处理逻辑
            finally:
                agent_pool.release(pooled_agent)
        
        if stream:
            return Response(generate(), mimetype='text/event-stream')
        else:
            try:
                # ... 处理逻辑
                return jsonify({"success": True, "session_id": session_id})
            finally:
                agent_pool.release(pooled_agent)
                
    except RuntimeError as e:
        if "Agent pool exhausted" in str(e):
            return jsonify({"error": "系统繁忙，请稍后再试"}), 503
        raise

# ========== /interrupt 接口 ==========
@app.route("/interrupt", methods=["POST"])
def interrupt():
    data = request.json or {}
    session_id = data.get("session_id")
    
    agent_pool = get_agent_pool()
    
    if session_id:
        success = agent_pool.cancel_session(session_id)
    else:
        # 兼容旧版本：取消任意一个正在运行的
        with agent_pool._lock:
            for pooled_agent in agent_pool._pool:
                if pooled_agent.in_use:
                    pooled_agent.agent.interrupt()
                    success = True
                    break
            else:
                success = False
    
    return jsonify({"success": success})
```

---

*文档版本: 1.0*
*最后更新: 2026-03-25*
