"""Harness Integration - 将 harness 组件与 SqlAgent 集成"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol

from .context.context_manager import ContextManager, ContextConfig, Message, MessageRole
from .tools.registry import ToolRegistry, ToolCall
from .tools.executor import ToolExecutor
from .state.session_state import SessionState, ExecutionRecord
from .state.checkpoint import CheckpointManager
from .error.retry import RetryManager, RetryPolicy, RetryStrategy
from .error.circuit_breaker import CircuitBreaker
from .memory.working_memory import WorkingMemory
from .memory.long_term_memory import LongTermMemory
from .memory.learning_memory import LearningMemory
from .filesystem.workspace import Workspace


class AgentInterface(Protocol):
    """Agent 接口协议"""

    def run(self, question: str, **kwargs) -> str:
        ...


@dataclass
class HarnessConfig:
    """Harness 集成配置"""
    enable_context_manager: bool = True
    enable_checkpoint: bool = True
    enable_retry: bool = True
    enable_circuit_breaker: bool = True
    enable_workspace: bool = True
    enable_learning: bool = True

    context_config: Optional[ContextConfig] = None
    retry_policy: Optional[RetryPolicy] = None

    checkpoint_dir: str = "./checkpoints"
    workspace_dir: str = "./workspace"
    learnings_dir: str = ".learnings"


class HarnessAgent:
    """
    Harness 集成 Agent

    将 harness 组件与 SqlAgent 集成，提供：
    1. 依赖注入 - 所有组件通过构造函数注入
    2. 生命周期管理 - 统一的初始化和清理
    3. 错误处理 - 重试 + 熔断
    4. 状态管理 - 检查点 + 恢复
    5. 上下文管理 - 防止 Context Rot
    """

    def __init__(
        self,
        agent: AgentInterface,
        config: Optional[HarnessConfig] = None
    ):
        self.config = config or HarnessConfig()
        self._agent = agent

        self._init_components()

    def _init_components(self) -> None:
        """初始化 harness 组件"""
        cfg = self.config

        if cfg.enable_context_manager:
            self.context_manager = ContextManager(cfg.context_config)
        else:
            self.context_manager = None

        if cfg.enable_checkpoint:
            self.checkpoint_manager = CheckpointManager(cfg.checkpoint_dir)
        else:
            self.checkpoint_manager = None

        if cfg.enable_retry:
            self.retry_manager = RetryManager(cfg.retry_policy or RetryPolicy())
        else:
            self.retry_manager = None

        if cfg.enable_circuit_breaker:
            self.circuit_breaker = CircuitBreaker()
        else:
            self.circuit_breaker = None

        if cfg.enable_workspace:
            self.workspace = Workspace(cfg.workspace_dir)
        else:
            self.workspace = None

        if cfg.enable_learning:
            self.learning_memory = LearningMemory(cfg.learnings_dir)
        else:
            self.learning_memory = None

        self.working_memory = WorkingMemory()
        self.session_state: Optional[SessionState] = None

    def __getattr__(self, name: str) -> Any:
        """代理底层 agent 的属性"""
        if name.startswith('_'):
            raise AttributeError(name)
        return getattr(self._agent, name)

    def run(
        self,
        question: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """运行 Agent（带 harness 保护）"""
        import uuid
        session_id = session_id or str(uuid.uuid4())

        self.session_state = SessionState(
            session_id=session_id,
            question=question,
            max_steps=kwargs.get("max_steps", 6)
        )

        if self.checkpoint_manager:
            self.checkpoint_manager.create_checkpoint(
                session_id=session_id,
                step=0,
                state=self.session_state,
                description="Initial state"
            )

        try:
            if self.circuit_breaker:
                result = self.circuit_breaker.call(self._run_with_retry, question, **kwargs)
            else:
                result = self._run_with_retry(question, **kwargs)

            self.session_state.complete()

            if self.checkpoint_manager:
                self.checkpoint_manager.create_checkpoint(
                    session_id=session_id,
                    step=self.session_state.current_step,
                    state=self.session_state,
                    description="Completed"
                )

            return result

        except Exception as e:
            self.session_state.last_error = str(e)
            self.session_state.cancel(str(e))

            if self.learning_memory:
                self.learning_memory.record_error(
                    error_type=type(e).__name__,
                    context=question,
                    solution=str(e)
                )

            if self.checkpoint_manager:
                self.checkpoint_manager.create_checkpoint(
                    session_id=session_id,
                    step=self.session_state.current_step,
                    state=self.session_state,
                    description=f"Failed: {e}"
                )

            raise

    def _run_with_retry(self, question: str, **kwargs) -> str:
        """带重试的运行"""
        if self.retry_manager:
            result, success, error = self.retry_manager.execute_with_retry(
                self._run_single,
                question=question,
                **kwargs
            )
            if success:
                return result
            raise error or Exception("Unknown error after retries")
        else:
            return self._run_single(question, **kwargs)

    def _run_single(self, question: str, **kwargs) -> str:
        """单次运行"""
        self.session_state.add_step("user", question)

        if self.context_manager:
            self.context_manager.add_message(MessageRole.USER, question)

        context_messages = None
        if self.context_manager:
            context_messages = self.context_manager.get_messages()

        if context_messages is not None and len(context_messages) > 0:
            result = self._agent.run(question, context_messages=context_messages, **kwargs)
        else:
            result = self._agent.run(question, **kwargs)

        if self.context_manager:
            self.context_manager.add_message(MessageRole.ASSISTANT, result)

        return result

    def recover(self, session_id: str) -> bool:
        """从检查点恢复"""
        if not self.checkpoint_manager:
            return False

        checkpoint = self.checkpoint_manager.get_latest_checkpoint(session_id)
        if not checkpoint:
            return False

        self.session_state = self.checkpoint_manager.restore_session_state(checkpoint)
        return True

    def get_state_summary(self) -> str:
        """获取状态摘要"""
        if not self.session_state:
            return "No active session"

        lines = [self.session_state.summary()]

        if self.context_manager:
            lines.append(f"Context tokens: {self.context_manager.count_total_tokens()}")

        if self.learning_memory:
            lines.append(self.learning_memory.summarize())

        return "\n".join(lines)


def create_harness_agent(
    agent: AgentInterface,
    enable_all: bool = True,
    **kwargs
) -> HarnessAgent:
    """
    创建 Harness Agent（便捷函数）

    Args:
        agent: 底层 Agent 实现
        enable_all: 是否启用所有 harness 功能
        **kwargs: HarnessConfig 参数

    Returns:
        HarnessAgent 实例
    """
    config = HarnessConfig(
        enable_context_manager=enable_all,
        enable_checkpoint=enable_all,
        enable_retry=enable_all,
        enable_circuit_breaker=enable_all,
        enable_workspace=enable_all,
        enable_learning=enable_all,
        **kwargs
    )
    return HarnessAgent(agent, config)
