"""Harness - Agent 运行时基础设施

提供上下文管理、工具注册、状态管理、记忆管理、错误恢复等核心能力。

核心组件：
- Context Manager: 解决 Context Rot 问题
- Tool Registry: 解决 Hallucinated Tool Calls 问题
- Session State + Checkpoint: 解决 Lost State on Failure 问题
- Retry + CircuitBreaker: 防止连续失败导致系统崩溃
- Workspace: 上下文卸载，释放上下文窗口
- Memory: 分层记忆管理（工作记忆、长期记忆、学习记忆）
- HarnessAgent: 依赖注入容器，连接所有组件
"""

from .context.context_manager import ContextManager, ContextConfig, Message, MessageRole
from .context.compressor import ContextCompressor
from .context.priority import MessagePriority, PriorityType
from .tools.registry import ToolRegistry, Tool, ToolCall, ToolResult, ActionType
from .tools.executor import ToolExecutor
from .tools.validator import ToolValidator
from .state.session_state import SessionState, Step, ExecutionRecord
from .state.checkpoint import CheckpointManager, Checkpoint
from .error.retry import RetryPolicy, RetryManager, RetryStrategy
from .error.circuit_breaker import CircuitBreaker, CircuitState, CircuitOpenError
from .memory.working_memory import WorkingMemory, MemoryItem
from .memory.long_term_memory import LongTermMemory, MemoryStore, MemoryState
from .memory.learning_memory import LearningMemory, ErrorPattern, SuccessPattern
from .filesystem.workspace import Workspace, Artifact
from .filesystem.artifacts import ArtifactManager
from .integration import HarnessAgent, HarnessConfig, AgentInterface, create_harness_agent

__all__ = [
    "ContextManager",
    "ContextConfig",
    "Message",
    "MessageRole",
    "ContextCompressor",
    "MessagePriority",
    "PriorityType",
    "ToolRegistry",
    "Tool",
    "ToolCall",
    "ToolResult",
    "ActionType",
    "ToolExecutor",
    "ToolValidator",
    "SessionState",
    "Step",
    "ExecutionRecord",
    "CheckpointManager",
    "Checkpoint",
    "RetryPolicy",
    "RetryManager",
    "RetryStrategy",
    "CircuitBreaker",
    "CircuitState",
    "CircuitOpenError",
    "WorkingMemory",
    "MemoryItem",
    "LongTermMemory",
    "MemoryStore",
    "MemoryState",
    "LearningMemory",
    "ErrorPattern",
    "SuccessPattern",
    "Workspace",
    "Artifact",
    "ArtifactManager",
    "HarnessAgent",
    "HarnessConfig",
    "AgentInterface",
    "create_harness_agent",
]