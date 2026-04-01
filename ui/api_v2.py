"""API v2 with service layer and agent pool support."""

from __future__ import annotations

import functools
import json
import os
import time
from typing import Any, Callable, Dict, Optional

from flask import Blueprint, jsonify, request, Response, g

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


def get_token_from_request() -> Optional[str]:
    """从请求中提取token
    
    支持:
    - Authorization: Bearer <token>
    - Cookie: session_token=<token>
    - Query param: ?token=<token>
    """
    # 从Header获取
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    # 从Cookie获取
    token = request.cookies.get("session_token")
    if token:
        return token
    
    # 从Query参数获取
    token = request.args.get("token")
    if token:
        return token
    
    return None


def get_auth_service():
    """获取认证服务实例"""
    from flask import current_app
    return getattr(current_app, "auth_service", None)


def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_service = get_auth_service()
        if not auth_service:
            return jsonify({
                "success": False,
                "error": "auth_service_not_initialized",
                "message": "Authentication service not initialized",
            }), 500
        
        token = get_token_from_request()
        if not token:
            return jsonify({
                "success": False,
                "error": "missing_token",
                "message": "Authentication token is required",
            }), 401
        
        user, error = auth_service.verify_token(token)
        if not user:
            return jsonify({
                "success": False,
                "error": "invalid_token",
                "message": error or "Invalid token",
            }), 401
        
        # 设置当前用户到Flask全局对象
        g.current_user = user
        g.current_token = token
        
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
        if report_path and os.path.exists(report_path):
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
            # 读取报告内容返回给前端
            report_content = ""
            report_path = result_holder["report_path"]
            if report_path and os.path.exists(report_path):
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        report_content = f.read()
                except Exception as e:
                    report_content = f"Error reading report: {e}"
            # 发送最终结果消息（前端期望 type: 'message'）
            yield f"data: {json.dumps({'type': 'message', 'role': 'assistant', 'content': report_content})}\n\n"
            # 发送完成标记
            yield f"data: {json.dumps({'type': 'done', 'report_path': report_path})}\n\n"
    
    return Response(generate(), mimetype="text/event-stream")


# =============================================================================
# Session Management
# =============================================================================

def _get_user_sessions_dir(user_id: str) -> str:
    """获取用户特定的会话目录"""
    from gold_miner.user_data import get_user_data_manager
    user_data_manager = get_user_data_manager()
    paths = user_data_manager.get_user_paths(user_id)
    return paths.sessions_dir


def _load_session_file(session_path: str) -> Optional[Dict]:
    """加载会话文件"""
    try:
        with open(session_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


@api_v2.route("/sessions", methods=["GET"])
@require_auth
@handle_errors
def list_sessions():
    """List all sessions for current user."""
    from flask import g
    user = g.current_user
    
    # 使用用户特定的会话目录
    sessions_dir = _get_user_sessions_dir(user.id)
    sessions = []
    
    if os.path.exists(sessions_dir):
        for filename in sorted(os.listdir(sessions_dir), reverse=True):
            if not filename.endswith(".json"):
                continue
            
            path = os.path.join(sessions_dir, filename)
            raw = _load_session_file(path)
            if raw:
                sessions.append({
                    "session_id": raw.get("session_id", filename[:-5]),
                    "title": raw.get("title", "未命名对话"),
                    "start_time": raw.get("start_time", ""),
                    "step_count": len(raw.get("steps", []))
                })
            
            if len(sessions) >= 50:
                break
    
    return jsonify({
        "success": True,
        "data": {"sessions": sessions},
    })


@api_v2.route("/sessions/<session_id>", methods=["GET"])
@require_auth
@handle_errors
def get_session(session_id: str):
    """Get session details for current user."""
    from flask import g
    user = g.current_user
    
    # 使用用户特定的会话目录
    sessions_dir = _get_user_sessions_dir(user.id)
    session_path = os.path.join(sessions_dir, f"{session_id}.json")
    
    if not os.path.exists(session_path):
        return jsonify({
            "success": False,
            "error": "session_not_found",
            "message": f"Session {session_id} not found or access denied",
        }), 404
    
    raw = _load_session_file(session_path)
    if not raw:
        return jsonify({
            "success": False,
            "error": "session_not_found",
            "message": f"Session {session_id} not found or access denied",
        }), 404
    
    # 验证用户权限
    session_user_id = raw.get("user_id", "")
    if session_user_id and session_user_id != user.id:
        return jsonify({
            "success": False,
            "error": "session_not_found",
            "message": f"Session {session_id} not found or access denied",
        }), 404
    
    steps = raw.get("steps", [])
    context = {
        "session_id": raw.get("session_id", session_id),
        "title": raw.get("title", "未命名对话"),
        "steps": steps,
        "step_count": len(steps),
        "final_result": raw.get("final_result"),  # 最终结果（用于会话切换后恢复）
        "result_status": raw.get("result_status", "pending"),  # 结果状态
    }

    return jsonify({
        "success": True,
        "data": {"session": context},
    })


@api_v2.route("/sessions/<session_id>", methods=["DELETE"])
@require_auth
@handle_errors
def delete_session_v2(session_id: str):
    """Delete a session for current user."""
    from flask import g
    user = g.current_user
    
    # 使用用户特定的会话目录
    sessions_dir = _get_user_sessions_dir(user.id)
    session_path = os.path.join(sessions_dir, f"{session_id}.json")
    
    if not os.path.exists(session_path):
        return jsonify({
            "success": False,
            "error": "session_not_found",
            "message": f"Session {session_id} not found or access denied",
        }), 404
    
    # 验证用户权限
    raw = _load_session_file(session_path)
    if raw:
        session_user_id = raw.get("user_id", "")
        if session_user_id and session_user_id != user.id:
            return jsonify({
                "success": False,
                "error": "session_not_found",
                "message": f"Session {session_id} not found or access denied",
            }), 404
    
    try:
        os.remove(session_path)
        return jsonify({
            "success": True,
            "data": {"deleted": True},
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "delete_failed",
            "message": str(e),
        }), 500


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


@api_v2.route("/llm/providers", methods=["GET"])
@require_auth
@handle_errors
def get_llm_providers():
    """Get LLM provider status."""
    from gold_miner.llm_provider import get_provider_manager
    
    manager = get_provider_manager()
    return jsonify({
        "success": True,
        "providers": manager.get_provider_status(),
    })


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


# =============================================================================
# Report Generation & Download
# =============================================================================

@api_v2.route("/sessions/<session_id>/dialogs", methods=["GET"])
@require_auth
@handle_errors
def get_session_dialogs(session_id: str):
    """获取会话中的对话列表（用户问题和助手回答，不包含任务日志）.
    
    Args:
        session_id: 会话ID
    
    Returns:
        {
            "success": true,
            "data": {
                "dialogs": [
                    {
                        "id": "对话ID",
                        "index": 0,
                        "user_message": "用户问题",
                        "assistant_message": "助手回答",
                        "timestamp": "时间戳"
                    }
                ]
            }
        }
    """
    from flask import g
    user = g.current_user
    
    # 加载会话数据
    sessions_dir = _get_user_sessions_dir(user.id)
    session_path = os.path.join(sessions_dir, f"{session_id}.json")
    
    if not os.path.exists(session_path):
        return jsonify({
            "success": False,
            "error": "session_not_found",
            "message": f"Session {session_id} not found",
        }), 404
    
    session_data = _load_session_file(session_path)
    if not session_data:
        return jsonify({
            "success": False,
            "error": "session_load_failed",
            "message": "Failed to load session data",
        }), 500
    
    # 验证用户权限
    session_user_id = session_data.get("user_id", "")
    if session_user_id and session_user_id != user.id:
        return jsonify({
            "success": False,
            "error": "access_denied",
            "message": "You don't have permission to access this session",
        }), 403
    
    # 提取对话列表（只包含 user 和 assistant，不包含 tool）
    steps = session_data.get("steps", [])
    dialogs = []
    current_dialog = None
    
    for i, step in enumerate(steps):
        role = step.get("role", "")
        content = step.get("content", "")
        timestamp = step.get("timestamp", "")
        
        if role == "user":
            # 保存上一个对话（如果存在）
            if current_dialog and current_dialog.get("user_message"):
                dialogs.append(current_dialog)
            # 开始新对话
            current_dialog = {
                "id": f"dialog_{len(dialogs)}",
                "index": len(dialogs),
                "user_message": content,
                "assistant_message": None,
                "timestamp": timestamp
            }
        elif role == "assistant" and current_dialog:
            # 提取助手回答（处理 JSON 格式）
            assistant_content = content
            if isinstance(content, str) and content.strip().startswith("{"):
                try:
                    parsed = json.loads(content)
                    if "report_markdown" in parsed:
                        assistant_content = parsed["report_markdown"]
                    elif "answer" in parsed:
                        assistant_content = parsed["answer"]
                    elif "content" in parsed:
                        assistant_content = parsed["content"]
                except json.JSONDecodeError:
                    pass
            current_dialog["assistant_message"] = assistant_content
    
    # 添加最后一个对话
    if current_dialog and current_dialog.get("user_message"):
        dialogs.append(current_dialog)
    
    # 如果存在最终结果但对话框中没有（可能是会话切换导致的），添加到最后一个对话框
    final_result = session_data.get("final_result")
    result_status = session_data.get("result_status", "pending")

    if final_result and dialogs and not dialogs[-1].get("assistant_message"):
        dialogs[-1]["assistant_message"] = final_result
    elif final_result and result_status == "completed" and not dialogs:
        # 如果没有对话框但有最终结果，创建一个完整的对话框
        dialogs.append({
            "id": "dialog_0",
            "index": 0,
            "user_message": session_data.get("title", "用户问题"),
            "assistant_message": final_result,
            "timestamp": session_data.get("start_time", "")
        })

    return jsonify({
        "success": True,
        "data": {
            "dialogs": dialogs,
            "session_id": session_id,
            "title": session_data.get("title", "未命名对话"),
            "final_result": final_result,  # 最终结果
            "result_status": result_status,  # 结果状态
        },
    })


@api_v2.route("/reports/formats", methods=["GET"])
@require_auth
@handle_errors
def list_report_formats():
    """获取支持的报告格式列表.
    
    Returns:
        支持的格式列表
    """
    formats = [
        {"id": "md", "name": "Markdown", "description": "Markdown 格式，适合查看和编辑"},
        {"id": "pdf", "name": "PDF", "description": "PDF 文档（即将支持）"},
        {"id": "xlsx", "name": "Excel", "description": "Excel 表格（即将支持）"},
    ]
    return jsonify({"success": True, "data": formats})


@api_v2.route("/reports/generate", methods=["POST"])
@require_auth
@handle_errors
def generate_report():
    """生成分析报告.
    
    Request Body:
        {
            "session_id": "会话ID",
            "format": "md",  // 格式：md, pdf, xlsx
            "title": "报告标题（可选）",
            "selected_dialogs": [0, 1, 2]  // 选中的对话索引列表（可选，默认全部）
        }
    
    Returns:
        {
            "success": true,
            "data": {
                "file_id": "文件ID",
                "filename": "报告文件名",
                "download_url": "下载链接",
                "size": 文件大小,
                "expire_at": "过期时间"
            }
        }
    """
    from gold_miner.report_generator import (
        ReportFormat,
        generate_report_from_session,
        generate_report_from_selected_dialogs,
    )
    from gold_miner.file_storage import create_user_storage_service
    
    data = request.json or {}
    session_id = data.get("session_id")
    format_str = data.get("format", "md")
    title = data.get("title")
    selected_dialogs = data.get("selected_dialogs")  # 选中的对话索引列表
    
    if not session_id:
        return jsonify({
            "success": False,
            "error": "missing_session_id",
            "message": "Session ID is required",
        }), 400
    
    # 获取当前用户
    user = g.current_user
    
    # 1. 加载会话数据
    sessions_dir = _get_user_sessions_dir(user.id)
    session_path = os.path.join(sessions_dir, f"{session_id}.json")
    
    if not os.path.exists(session_path):
        return jsonify({
            "success": False,
            "error": "session_not_found",
            "message": f"Session {session_id} not found",
        }), 404
    
    session_data = _load_session_file(session_path)
    if not session_data:
        return jsonify({
            "success": False,
            "error": "session_load_failed",
            "message": "Failed to load session data",
        }), 500
    
    # 验证用户权限
    session_user_id = session_data.get("user_id", "")
    if session_user_id and session_user_id != user.id:
        return jsonify({
            "success": False,
            "error": "access_denied",
            "message": "You don't have permission to access this session",
        }), 403
    
    # 2. 确定报告格式
    try:
        report_format = ReportFormat(format_str)
    except ValueError:
        return jsonify({
            "success": False,
            "error": "invalid_format",
            "message": f"Unsupported format: {format_str}. Supported: md",
        }), 400
    
    # 3. 获取用户报告目录
    from gold_miner.user_data import get_user_data_manager
    user_data_manager = get_user_data_manager()
    user_paths = user_data_manager.get_user_paths(user.id)
    reports_dir = user_paths.reports_dir
    
    # 确保目录存在
    os.makedirs(reports_dir, exist_ok=True)
    
    # 4. 生成报告文件
    # 尝试获取 LLM 客户端进行智能总结
    llm_client = None
    try:
        from gold_miner.llm_provider import get_provider_manager
        llm_manager = get_provider_manager()
        if llm_manager:
            # 创建一个简单的包装器，适配 LLM 接口
            class LLMClientWrapper:
                def __init__(self, manager):
                    self.manager = manager
                
                def chat(self, prompt: str) -> str:
                    messages = [{"role": "user", "content": prompt}]
                    return self.manager.chat(messages, temperature=0.3)
            
            llm_client = LLMClientWrapper(llm_manager)
            print(f"[APIv2] LLM client initialized successfully")
    except Exception as e:
        print(f"[APIv2] LLM client not available for report generation: {e}")
    
    try:
        # 如果指定了选中的对话，使用新的生成方法
        if selected_dialogs is not None and isinstance(selected_dialogs, list):
            report_path = generate_report_from_selected_dialogs(
                session_data=session_data,
                selected_indices=selected_dialogs,
                output_dir=reports_dir,
                title=title,
                fmt=report_format,
                llm_client=llm_client,
            )
        else:
            # 否则使用原来的方法（生成全部对话的报告）
            report_path = generate_report_from_session(
                session_data=session_data,
                output_dir=reports_dir,
                title=title,
                fmt=report_format,
                llm_client=llm_client,
            )
    except NotImplementedError as e:
        return jsonify({
            "success": False,
            "error": "format_not_implemented",
            "message": str(e),
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "generate_failed",
            "message": f"Failed to generate report: {str(e)}",
        }), 500
    
    # 5. 存储到文件服务
    storage_service = create_user_storage_service(
        user_reports_dir=reports_dir,
        base_url=f"/api/v2/reports/download",
        expire_hours=24,
    )
    
    file_info = storage_service.store_file(
        local_path=report_path,
        original_filename=os.path.basename(report_path),
        expire_hours=24,
        use_original_name=True,  # 使用原始文件名作为 file_id
    )
    
    return jsonify({
        "success": True,
        "data": {
            "file_id": file_info.file_id,
            "filename": file_info.filename,
            "download_url": file_info.download_url,
            "size": file_info.size,
            "expire_at": file_info.expire_at.isoformat(),
        },
    })


@api_v2.route("/reports/download/<file_id>", methods=["GET"])
@require_auth
@handle_errors
def download_report(file_id: str):
    """下载报告文件.
    
    Args:
        file_id: 文件ID
    
    Query Params:
        download: 是否作为附件下载（1=下载，0=预览）
    
    Returns:
        文件内容
    """
    from gold_miner.file_storage import create_user_storage_service
    from flask import send_file
    
    # 获取当前用户
    user = g.current_user
    
    # 获取用户报告目录
    from gold_miner.user_data import get_user_data_manager
    user_data_manager = get_user_data_manager()
    user_paths = user_data_manager.get_user_paths(user.id)
    reports_dir = user_paths.reports_dir
    
    # 创建存储服务
    storage_service = create_user_storage_service(
        user_reports_dir=reports_dir,
        base_url=f"/api/v2/reports/download",
    )
    
    # 获取文件信息
    file_info = storage_service.get_file_info(file_id)
    if not file_info:
        # 如果不在内存中，尝试直接从文件系统查找
        # 对于使用原始文件名的报告，file_id 就是文件名（不含扩展名）
        file_path = None
        
        # 尝试直接查找 file_id.md
        direct_path = os.path.join(reports_dir, f"{file_id}.md")
        if os.path.exists(direct_path):
            file_path = direct_path
        
        # 如果没找到，尝试遍历目录查找匹配的文件
        if not file_path and os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                # 检查文件名是否以 file_id 开头（原始文件名格式: {title}_{timestamp}.md）
                if filename.startswith(file_id) or filename.replace('.md', '') == file_id:
                    file_path = os.path.join(reports_dir, filename)
                    break
        
        if not file_path:
            return jsonify({
                "success": False,
                "error": "file_not_found",
                "message": "File not found or expired",
            }), 404
        
        # 重新创建文件信息，使用原始文件名
        actual_filename = os.path.basename(file_path)
        file_info = storage_service.store_file(
            local_path=file_path,
            original_filename=actual_filename,
            use_original_name=True,
        )
    
    # 检查文件是否存在
    if not os.path.exists(file_info.file_path):
        return jsonify({
            "success": False,
            "error": "file_not_found",
            "message": "File not found on server",
        }), 404
    
    # 设置响应头
    as_attachment = request.args.get("download", "0") == "1"
    
    return send_file(
        file_info.file_path,
        mimetype=file_info.content_type,
        as_attachment=as_attachment,
        download_name=file_info.filename,
    )


@api_v2.route("/reports/list", methods=["GET"])
@require_auth
@handle_errors
def list_user_reports():
    """列出用户的报告文件.
    
    Returns:
        报告文件列表
    """
    from gold_miner.file_storage import create_user_storage_service
    
    # 获取当前用户
    user = g.current_user
    
    # 获取用户报告目录
    from gold_miner.user_data import get_user_data_manager
    user_data_manager = get_user_data_manager()
    user_paths = user_data_manager.get_user_paths(user.id)
    reports_dir = user_paths.reports_dir
    
    # 扫描目录中的报告文件
    reports = []
    if os.path.exists(reports_dir):
        for filename in sorted(os.listdir(reports_dir), reverse=True):
            if filename.endswith(".md"):
                file_path = os.path.join(reports_dir, filename)
                stat = os.stat(file_path)
                
                # 从文件名提取信息
                # 格式: {title}_{timestamp}.md
                name_parts = filename.rsplit("_", 1)
                title = name_parts[0] if len(name_parts) > 1 else filename
                
                reports.append({
                    "filename": filename,
                    "title": title,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "download_url": f"/api/v2/reports/download/{filename[:-3]}",
                })
    
    return jsonify({
        "success": True,
        "data": {
            "reports": reports,
            "total": len(reports),
        },
    })
