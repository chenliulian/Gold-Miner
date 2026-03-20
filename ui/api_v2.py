"""API v2 with service layer and agent pool support."""

from __future__ import annotations

import functools
import json
import time
from typing import Any, Callable, Dict, Optional

from flask import Blueprint, jsonify, request, Response

from gold_miner.config import Config
from gold_miner.rate_limiter import RateLimitExceeded
from gold_miner.services import get_agent_pool, get_task_queue

# Create blueprint
api_v2 = Blueprint("api_v2", __name__, url_prefix="/api/v2")

# Global config
_config: Optional[Config] = None


def init_config(config: Config) -> None:
    """Initialize configuration."""
    global _config
    _config = config


def get_client_ip() -> str:
    """Get client IP address from request."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    elif request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP")
    else:
        return request.remote_addr


def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # Add API key validation here if needed
        return f(*args, **kwargs)
    return decorated


def handle_errors(f: Callable) -> Callable:
    """Decorator to handle common errors."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except RateLimitExceeded as e:
            return jsonify({
                "success": False,
                "error": "rate_limit_exceeded",
                "message": str(e),
            }), 429
        except Exception as e:
            return jsonify({
                "success": False,
                "error": "internal_error",
                "message": str(e),
            }), 500
    return decorated


# =============================================================================
# Agent Pool Endpoints
# =============================================================================

@api_v2.route("/agents", methods=["GET"])
@handle_errors
def list_agents():
    """List all agents in the pool."""
    pool = get_agent_pool()
    stats = pool.get_stats()
    return jsonify({
        "success": True,
        "data": stats,
    })


@api_v2.route("/agents/cleanup", methods=["POST"])
@handle_errors
def cleanup_agents():
    """Cleanup idle agents."""
    pool = get_agent_pool()
    removed = pool.cleanup_idle()
    return jsonify({
        "success": True,
        "data": {"removed": removed},
    })


# =============================================================================
# Task Queue Endpoints
# =============================================================================

@api_v2.route("/tasks", methods=["POST"])
@handle_errors
def submit_task():
    """Submit a new task to the queue."""
    data = request.json or {}
    question = data.get("question", "")
    
    if not question:
        return jsonify({
            "success": False,
            "error": "missing_question",
            "message": "Question is required",
        }), 400

    queue = get_task_queue()
    
    def run_task():
        """Execute the task."""
        pool = get_agent_pool()
        agent_wrapper = pool.acquire()
        try:
            result = agent_wrapper.agent.run(question)
            return {"status": "completed", "result": result}
        finally:
            pool.release(agent_wrapper)
    
    task_id = queue.submit(run_task)
    
    return jsonify({
        "success": True,
        "data": {
            "task_id": task_id,
            "status": "pending",
        },
    }), 202


@api_v2.route("/tasks/<task_id>", methods=["GET"])
@handle_errors
def get_task_status(task_id: str):
    """Get task status."""
    queue = get_task_queue()
    status = queue.get_status(task_id)
    
    if not status:
        return jsonify({
            "success": False,
            "error": "task_not_found",
            "message": f"Task {task_id} not found",
        }), 404
    
    return jsonify({
        "success": True,
        "data": status,
    })


@api_v2.route("/tasks/<task_id>/cancel", methods=["POST"])
@handle_errors
def cancel_task(task_id: str):
    """Cancel a pending task."""
    queue = get_task_queue()
    cancelled = queue.cancel(task_id)
    
    return jsonify({
        "success": True,
        "data": {"cancelled": cancelled},
    })


@api_v2.route("/tasks/stats", methods=["GET"])
@handle_errors
def get_queue_stats():
    """Get task queue statistics."""
    queue = get_task_queue()
    stats = queue.get_stats()
    
    return jsonify({
        "success": True,
        "data": stats,
    })


# =============================================================================
# Chat Endpoints (with Agent Pool)
# =============================================================================

@api_v2.route("/chat", methods=["POST"])
@handle_errors
def chat():
    """Chat endpoint using agent pool."""
    data = request.json or {}
    question = data.get("question", "")
    
    if not question:
        return jsonify({
            "success": False,
            "error": "missing_question",
            "message": "Question is required",
        }), 400

    # Acquire agent from pool
    pool = get_agent_pool()
    agent_wrapper = pool.acquire()
    
    try:
        # Start new session
        session_title = question[:30] + "..." if len(question) > 30 else question
        agent_wrapper.agent.start_new_session(title=session_title)
        
        # Run agent
        report_path = agent_wrapper.agent.run(question)
        
        # Read report
        response_text = ""
        if report_path and json.os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                response_text = f.read()
        
        return jsonify({
            "success": True,
            "data": {
                "response": response_text,
                "report_path": report_path,
                "agent_id": agent_wrapper.agent_id,
            },
        })
    finally:
        pool.release(agent_wrapper)


@api_v2.route("/chat/stream", methods=["POST"])
@handle_errors
def chat_stream():
    """Streaming chat endpoint."""
    data = request.json or {}
    question = data.get("question", "")
    
    if not question:
        return jsonify({
            "success": False,
            "error": "missing_question",
            "message": "Question is required",
        }), 400

    def generate():
        import queue
        import threading
        
        log_queue = queue.Queue()
        result_holder = {"report_path": None, "error": None, "done": False}
        
        def status_callback(status):
            if isinstance(status, dict):
                log_queue.put({"type": "log", "content": status.get("content", str(status))})
            elif status == "starting":
                log_queue.put({"type": "log", "content": "Starting task..."})
            elif status == "finalizing":
                log_queue.put({"type": "log", "content": "Generating report..."})
            elif status == "done":
                log_queue.put({"type": "log", "content": "Task completed"})
            elif status == "cancelled":
                log_queue.put({"type": "log", "content": "Task cancelled"})
        
        def run_agent():
            try:
                pool = get_agent_pool()
                agent_wrapper = pool.acquire()
                try:
                    report_path = agent_wrapper.agent.run(
                        question,
                        status_cb=status_callback,
                        clear_memory=False,
                    )
                    result_holder["report_path"] = report_path
                    result_holder["done"] = True
                finally:
                    pool.release(agent_wrapper)
            except Exception as e:
                result_holder["error"] = str(e)
                result_holder["done"] = True
        
        # Start agent thread
        agent_thread = threading.Thread(target=run_agent)
        agent_thread.start()
        
        # Stream logs
        while not result_holder["done"] or not log_queue.empty():
            try:
                log_data = log_queue.get(timeout=0.1)
                yield f"data: {json.dumps(log_data)}\n\n"
            except queue.Empty:
                if result_holder["done"] and log_queue.empty():
                    break
                continue
        
        agent_thread.join()
        
        # Send final result
        if result_holder["error"]:
            yield f"data: {json.dumps({'type': 'error', 'content': result_holder['error']})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'done', 'report_path': result_holder['report_path']})}\n\n"
    
    return Response(generate(), mimetype="text/event-stream")


# =============================================================================
# Session Management
# =============================================================================

@api_v2.route("/sessions", methods=["GET"])
@handle_errors
def list_sessions():
    """List all sessions."""
    pool = get_agent_pool()
    agent_wrapper = pool.acquire()
    try:
        sessions = agent_wrapper.agent.session.list_sessions(limit=50)
        return jsonify({
            "success": True,
            "data": {"sessions": sessions},
        })
    finally:
        pool.release(agent_wrapper)


@api_v2.route("/sessions/<session_id>", methods=["GET"])
@handle_errors
def get_session(session_id: str):
    """Get session details."""
    pool = get_agent_pool()
    agent_wrapper = pool.acquire()
    try:
        success = agent_wrapper.agent.session.load_session(session_id)
        if not success:
            return jsonify({
                "success": False,
                "error": "session_not_found",
                "message": f"Session {session_id} not found",
            }), 404
        
        context = agent_wrapper.agent.session.get_context()
        return jsonify({
            "success": True,
            "data": {"session": context},
        })
    finally:
        pool.release(agent_wrapper)


# =============================================================================
# Health & Metrics
# =============================================================================

@api_v2.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    try:
        pool = get_agent_pool()
        queue = get_task_queue()
        
        return jsonify({
            "status": "healthy",
            "timestamp": time.time(),
            "components": {
                "agent_pool": pool.get_stats(),
                "task_queue": queue.get_stats(),
            },
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time(),
        }), 503


@api_v2.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus-style metrics."""
    try:
        from gold_miner.circuit_breaker import get_all_circuit_breakers
        
        pool = get_agent_pool()
        queue = get_task_queue()
        lines = []
        
        # Agent pool metrics
        pool_stats = pool.get_stats()
        lines.append('# HELP goldminer_pool_agents_total Total agents in pool')
        lines.append('# TYPE goldminer_pool_agents_total gauge')
        lines.append(f'goldminer_pool_agents_total {pool_stats["total_agents"]}')
        lines.append(f'goldminer_pool_agents_in_use {pool_stats["in_use"]}')
        lines.append(f'goldminer_pool_agents_available {pool_stats["available"]}')
        
        # Task queue metrics
        queue_stats = queue.get_stats()
        lines.append('# HELP goldminer_queue_size Task queue size')
        lines.append('# TYPE goldminer_queue_size gauge')
        lines.append(f'goldminer_queue_size {queue_stats["queue_size"]}')
        lines.append(f'goldminer_queue_total_tasks {queue_stats["total_tasks"]}')
        
        # Circuit breaker metrics
        for name, breaker in get_all_circuit_breakers().items():
            stats = breaker.get_stats()
            state_value = 1 if stats["state"] == "closed" else 0
            lines.append(f'goldminer_circuit_breaker_state{{name="{name}"}} {state_value}')
            lines.append(f'goldminer_circuit_breaker_failures{{name="{name}"}} {stats["failure_count"]}')
        
        return '\n'.join(lines), 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        return f"# Error: {e}", 500
