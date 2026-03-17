from __future__ import annotations

import argparse
import os
import sys
import threading
import queue
import time

def safe_input(prompt=""):
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
    parser = argparse.ArgumentParser(description="gold-miner SQL analysis agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    analyze = sub.add_parser("analyze", help="Run SQL analysis with agent (one-shot)")
    analyze.add_argument("--question", required=True, help="Analysis request")
    analyze.add_argument("--tables", default="", help="Comma-separated table list")
    analyze.add_argument("--max-steps", type=int, default=None, help="Max agent steps")
    analyze.add_argument("--output", default=None, help="Output report path")

    chat = sub.add_parser("chat", help="Interactive chat mode")
    chat.add_argument("--max-steps", type=int, default=None, help="Max agent steps")

    args = parser.parse_args()

    if args.cmd == "analyze":
        cfg = Config.from_env()
        cfg.validate()
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        skills_dir = os.path.join(project_root, "skills")
        agent = SqlAgent(cfg, skills_dir)
        report_path = agent.run(
            question=args.question,
            tables=args.tables,
            max_steps=args.max_steps,
            output_path=args.output,
        )
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            print(content)
        finally:
            print(f"\nReport saved to: {report_path}")
        return

    if args.cmd == "chat":
        cfg = Config.from_env()
        cfg.validate()
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        skills_dir = os.path.join(project_root, "skills")
        print(f"[Debug] project_root: {project_root}, skills_dir: {skills_dir}, exists: {os.path.exists(skills_dir)}")
        agent = SqlAgent(cfg, skills_dir)
        print(
            "gold-miner chat mode. Type 'exit' to quit. "
            "Commands: /reset, /status, /cancel"
        )
        print(f"[Debug] Loaded {len(agent.skills.skills)} skills: {list(agent.skills.skills.keys())}")
        task_queue: queue.Queue[tuple[str, str] | None] = queue.Queue()
        status_lock = threading.Lock()
        state = {"status": "idle", "current": None, "last_report": None, "cancel": None}
        exit_event = threading.Event()  # Signal for worker to exit immediately

        def _do_exit() -> None:
            """Signal worker thread to exit and cancel any running task."""
            with status_lock:
                cancel_event = state["cancel"]
            if cancel_event is not None:
                print("Cancelling running task...")
                cancel_event.set()
            exit_event.set()
            task_queue.put(None)  # Wake up worker if waiting
            time.sleep(0.3)  # Give it a moment to respond

        def set_status(value: str) -> None:
            with status_lock:
                state["status"] = value

        def worker() -> None:
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
                        max_steps=args.max_steps,
                        output_path=None,
                        cancel_event=cancel_event,
                        status_cb=set_status,
                    )
                    if report_path:
                        with open(report_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        print("\n" + content)
                        print(f"\nReport saved to: {report_path}")
                        print("\n" + "="*50)
                        print("You can continue asking questions or type 'exit' to quit.")
                        print("="*50)
                        with status_lock:
                            state["last_report"] = report_path
                except LLMError as exc:
                    print(f"\nLLM error: {exc}")
                    print("You can retry your question or check LLM settings in .env.")
                finally:
                    with status_lock:
                        state["status"] = "idle"
                        state["current"] = None
                        state["cancel"] = None
                task_queue.task_done()

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        while True:
            try:
                question = safe_input("\nQuestion> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye.")
                _do_exit()
                break
            if not question or question.lower() in {"exit", "quit"}:
                print("Bye.")
                _do_exit()
                break
            if question.strip().lower() == "/reset":
                agent.memory.clear()
                print("Memory cleared.")
                continue
            if question.strip().lower() == "/status":
                with status_lock:
                    status = state["status"]
                    current = state["current"]
                if status == "idle":
                    print("Status: idle")
                else:
                    print(f"Status: {status}")
                    if current:
                        print(f"Current question: {current['question']}")
                        if current["tables"]:
                            print(f"Current tables: {current['tables']}")
                continue
            if question.strip().lower() == "/cancel":
                with status_lock:
                    cancel_event = state["cancel"]
                    current_status = state["status"]
                if cancel_event is None:
                    print("Nothing to cancel.")
                else:
                    cancel_event.set()
                    print("Cancel requested. It will stop after the current step.")
                    # Wait for worker to become idle
                    print("Waiting for current task to stop...")
                    for _ in range(60):  # Wait up to 30 seconds
                        with status_lock:
                            if state["status"] == "idle":
                                break
                        time.sleep(0.5)
                    with status_lock:
                        if state["status"] != "idle":
                            print("Warning: Task may still be running in background.")
                        else:
                            print("Task cancelled. Ready for new questions.")
                continue
            
            # Check if worker is busy before accepting new task
            with status_lock:
                if state["status"] != "idle":
                    print(f"Cannot start new task: current status is '{state['status']}'")
                    print("Please wait for the current task to complete or use /cancel to stop it.")
                    continue
            
            tables = safe_input("Tables (comma-separated, optional)> ").strip()
            if tables.lower().startswith("from "):
                tables = tables[5:].strip()
            task_queue.put((question, tables))


if __name__ == "__main__":
    main()
