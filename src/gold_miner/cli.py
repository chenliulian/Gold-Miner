"""GoldMiner CLI - 交互式聊天模式

简化版 CLI，只保留聊天模式，自动从知识库识别相关表。
"""
from __future__ import annotations

import os
import sys
import threading
import queue
import time


def safe_input(prompt=""):
    """安全地获取用户输入"""
    try:
        return input(prompt)
    except UnicodeDecodeError:
        return input(prompt.encode('utf-8', errors='replace').decode('utf-8'))


if __package__ is None or __package__ == "":
    # Allow running as a script: `python3 src/gold_miner/cli.py`
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gold_miner.agent import SqlAgent
from gold_miner.config import Config
from gold_miner.llm import LLMError


def main() -> None:
    """主函数 - 启动交互式聊天模式"""
    # 加载配置
    cfg = Config.from_env()
    cfg.validate()
    
    # 初始化 Agent
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    skills_dir = os.path.join(project_root, "skills")
    agent = SqlAgent(cfg, skills_dir)
    
    # 打印欢迎信息
    print("=" * 60)
    print("🤖 GoldMiner SQL 分析助手")
    print("=" * 60)
    print("\n直接输入你的问题，我会自动分析并生成 SQL 查询。")
    print("\n可用命令:")
    print("  /reset   - 清空对话历史")
    print("  /status  - 查看当前状态")
    print("  /cancel  - 取消正在执行的任务")
    print("  exit     - 退出程序")
    print("\n" + "=" * 60)
    
    # 任务队列和状态管理
    task_queue: queue.Queue[tuple[str, str] | None] = queue.Queue()
    status_lock = threading.Lock()
    state = {"status": "idle", "current": None, "last_report": None, "cancel": None}
    exit_event = threading.Event()

    def _do_exit() -> None:
        """退出程序"""
        with status_lock:
            cancel_event = state["cancel"]
        if cancel_event is not None:
            print("正在取消运行中的任务...")
            cancel_event.set()
        exit_event.set()
        task_queue.put(None)
        time.sleep(0.3)

    def set_status(value) -> None:
        """更新状态 - 支持字符串或字典"""
        with status_lock:
            # 如果 value 是字典，提取状态类型
            if isinstance(value, dict):
                state["status"] = value.get("type", "running")
                state["status_detail"] = value
            else:
                state["status"] = value
                state["status_detail"] = None

    def worker() -> None:
        """工作线程 - 处理任务队列"""
        while not exit_event.is_set():
            try:
                item = task_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if item is None or exit_event.is_set():
                break
            
            question, tables = item
            cancel_event = threading.Event()
            with status_lock:
                state["status"] = "running"
                state["current"] = {"question": question, "tables": tables}
                state["cancel"] = cancel_event
            
            try:
                report_path = agent.run(
                    question=question,
                    tables=tables,
                    max_steps=cfg.agent_max_steps,
                    output_path=None,
                    cancel_event=cancel_event,
                    status_cb=set_status,
                    clear_memory=False,  # 聊天模式下不清空记忆，保持对话上下文
                )
                if report_path:
                    with open(report_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    print("\n" + content)
                    print(f"\n📄 报告已保存: {report_path}")
                    print("\n" + "-" * 60)
                    print("可以继续提问，或输入 exit 退出")
                    print("-" * 60)
                    with status_lock:
                        state["last_report"] = report_path
            except LLMError as exc:
                print(f"\n❌ LLM 错误: {exc}")
                print("请检查 .env 中的 LLM 配置或重试")
            finally:
                with status_lock:
                    state["status"] = "idle"
                    state["current"] = None
                    state["cancel"] = None
            task_queue.task_done()

    # 启动工作线程
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    
    # 主循环
    while True:
        try:
            question = safe_input("\n💬 ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            _do_exit()
            break
        
        if not question:
            continue
        
        if question.lower() in {"exit", "quit", "退出"}:
            print("再见！")
            _do_exit()
            break
        
        # 处理命令
        if question == "/reset":
            agent.memory.clear()
            print("✅ 对话历史已清空")
            continue
        
        if question == "/status":
            with status_lock:
                status = state["status"]
                status_detail = state.get("status_detail")
                current = state["current"]
            if status == "idle":
                print("📍 状态: 空闲")
            else:
                # 如果有详细状态信息，显示更友好的内容
                if status_detail and isinstance(status_detail, dict):
                    content = status_detail.get("content", "")
                    if len(content) > 100:
                        content = content[:100] + "..."
                    print(f"📍 状态: {status} - {content}")
                else:
                    print(f"📍 状态: {status}")
                if current:
                    print(f"📝 当前问题: {current['question']}")
            continue
        
        if question == "/cancel":
            with status_lock:
                cancel_event = state["cancel"]
                current_status = state["status"]
            if cancel_event is None:
                print("⚠️ 没有正在运行的任务")
            else:
                cancel_event.set()
                print("⏹️  正在取消任务...")
                # 等待任务完成或超时（最多60秒）
                cancelled = False
                for i in range(120):  # 120 * 0.5 = 60秒
                    with status_lock:
                        current_st = state["status"]
                        # 检查状态是否为 idle 或 done（agent 完成时会设置 done）
                        if current_st in ("idle", "done", "cancelled"):
                            cancelled = True
                            break
                    time.sleep(0.5)
                with status_lock:
                    if not cancelled:
                        print("⚠️ 任务可能仍在后台运行")
                    else:
                        # 重置状态为 idle，允许新任务
                        state["status"] = "idle"
                        state["cancel"] = None
                        state["current"] = None
                        print("✅ 任务已取消，可以继续提问")
            continue
        
        # 检查是否忙碌
        with status_lock:
            if state["status"] != "idle":
                print(f"⚠️ 当前状态 '{state['status']}'，请先等待或输入 /cancel 取消")
                continue
        
        # 提交任务（不再询问表名，由 Agent 自动识别）
        task_queue.put((question, ""))


if __name__ == "__main__":
    main()
