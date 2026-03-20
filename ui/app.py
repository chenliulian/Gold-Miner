import json
import os
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session, Response
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

from gold_miner.config import Config

# Validate and set session secret before creating app
_config = Config.from_env()
_config.validate_security()
app.secret_key = _config.session_secret

from gold_miner.agent import SqlAgent
from gold_miner.rate_limiter import RateLimitExceeded, get_chat_limiter, get_default_limiter

# Import and register API v2
from api_v2 import api_v2, init_config
init_config(_config)
app.register_blueprint(api_v2)

CONFIG = None
AGENT = None


def get_client_ip():
    """Get client IP address from request."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def check_rate_limit(limiter_type="default"):
    """Check rate limit for current request."""
    client_ip = get_client_ip()
    
    if limiter_type == "chat":
        limiter = get_chat_limiter()
    else:
        limiter = get_default_limiter()
    
    allowed, info = limiter.is_allowed(client_ip)
    
    if not allowed:
        raise RateLimitExceeded(
            f"Rate limit exceeded. Please try again after {int(info['reset'] - time.time())} seconds."
        )
    
    return info


def get_agent():
    global AGENT, CONFIG
    if AGENT is None:
        CONFIG = _config
        CONFIG.validate()
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skills_dir = os.path.join(project_root, "skills")
        # 会话文件保存到 ui/sessions 目录
        sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")
        AGENT = SqlAgent(CONFIG, skills_dir, sessions_dir=sessions_dir)
        
        # Initialize agent pool for API v2
        from gold_miner.services import get_agent_pool
        get_agent_pool(
            config=CONFIG,
            skills_dir=skills_dir,
            sessions_dir=sessions_dir,
        )
    
    return AGENT


def init_schedulers():
    """Initialize background schedulers based on config."""
    if not _config.scheduler_auto_start:
        print("[App] Scheduler auto-start is disabled")
        return

    from gold_miner.learning_reviewer import get_learning_reviewer
    from gold_miner.session_summarizer import get_session_summarizer

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    get_learning_reviewer(
        learnings_dir=os.path.join(project_root, "skills/self_improvement/references"),
        memory_path=os.path.join(project_root, "memory/memory.md"),
        review_interval_hours=_config.scheduler_review_interval_hours,
        auto_start=True,
    )

    get_session_summarizer(
        sessions_dir=os.path.join(project_root, "sessions"),
        memory_path=os.path.join(project_root, "memory/memory.json"),
        review_interval_hours=_config.scheduler_session_review_hours,
        auto_start=True,
    )

    print(f"[App] Schedulers started: review_interval={_config.scheduler_review_interval_hours}h, session_review={_config.scheduler_session_review_hours}h")


# Initialize schedulers after all functions are defined
init_schedulers()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    # Check rate limit for chat endpoint
    try:
        rate_info = check_rate_limit("chat")
    except RateLimitExceeded as e:
        return jsonify({"error": str(e)}), 429
    
    data = request.json
    user_message = data.get("message", "")
    stream = data.get("stream", False)
    new_session = data.get("new_session", False)  # 是否开启新会话
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    agent = get_agent()
    
    # 如果需要开启新会话
    if new_session or agent.session.get_current_session_id() is None:
        session_title = user_message[:30] + "..." if len(user_message) > 30 else user_message
        agent.start_new_session(title=session_title)
    
    def generate():
        import queue
        import threading
        
        log_queue = queue.Queue()
        result_holder = {"report_path": None, "error": None, "done": False}
        
        def status_callback(status):
            """状态回调函数，将日志放入队列"""
            if isinstance(status, dict):
                log_queue.put({"type": "log", "content": status.get("content", str(status))})
            elif status == "starting":
                log_queue.put({"type": "log", "content": "🚀 开始处理任务..."})
            elif status == "finalizing":
                log_queue.put({"type": "log", "content": "📝 生成报告..."})
            elif status == "done":
                log_queue.put({"type": "log", "content": "✅ 任务完成"})
            elif status == "cancelled":
                log_queue.put({"type": "log", "content": "🛑 任务已取消"})
        
        def run_agent():
            """在后台线程中运行 agent"""
            try:
                agent.session.add_step("user", user_message)
                report_path = agent.run(user_message, status_cb=status_callback, clear_memory=False)
                result_holder["report_path"] = report_path
                result_holder["done"] = True
            except Exception as e:
                import traceback
                traceback.print_exc()
                result_holder["error"] = str(e)
                result_holder["done"] = True
        
        # 启动 agent 线程
        agent_thread = threading.Thread(target=run_agent)
        agent_thread.start()
        
        # 发送用户消息确认
        yield f"data: {json.dumps({'type': 'message', 'role': 'user', 'content': user_message})}\n\n"
        
        # 循环读取日志队列
        while not result_holder["done"] or not log_queue.empty():
            try:
                # 等待日志消息，最多等待 0.1 秒
                log_data = log_queue.get(timeout=0.1)
                yield f"data: {json.dumps(log_data)}\n\n"
            except queue.Empty:
                # 检查 agent 是否完成
                if result_holder["done"] and log_queue.empty():
                    break
                continue
        
        # 等待 agent 线程完成
        agent_thread.join()
        
        # 处理结果
        if result_holder["error"]:
            yield f"data: {json.dumps({'type': 'error', 'content': result_holder['error']})}\n\n"
        else:
            report_path = result_holder["report_path"]
            response_text = ""
            
            if report_path and os.path.exists(report_path):
                with open(report_path, "r", encoding="utf-8") as f:
                    response_text = f.read()
            else:
                response_text = str(report_path) if report_path else "任务完成"
            
            agent.session.add_step("assistant", response_text)
            
            yield f"data: {json.dumps({'type': 'message', 'role': 'assistant', 'content': response_text})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    if stream:
        return Response(generate(), mimetype='text/event-stream')
    
    # Non-streaming mode
    try:
        agent.session.add_step("user", user_message)
        
        report_path = agent.run(user_message)
        
        response_text = ""
        if report_path and os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                response_text = f.read()
        else:
            response_text = str(report_path) if report_path else "任务完成"
        
        agent.session.add_step("assistant", response_text)
        
        return jsonify({
            "success": True,
            "response": response_text,
            "report_path": report_path,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/sessions", methods=["GET"])
def list_sessions():
    """获取所有历史会话列表"""
    agent = get_agent()
    
    try:
        sessions = agent.session.list_sessions(limit=50)
        return jsonify({
            "success": True,
            "sessions": sessions
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
    """获取特定会话的详情"""
    agent = get_agent()
    
    try:
        # 临时加载指定会话
        success = agent.session.load_session(session_id)
        if not success:
            return jsonify({
                "success": False,
                "error": "Session not found"
            }), 404
        
        context = agent.session.get_context()
        return jsonify({
            "success": True,
            "session": context
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/sessions/new", methods=["POST"])
def new_session():
    """开启新会话"""
    agent = get_agent()
    
    try:
        data = request.json or {}
        title = data.get("title", "")
        session_id = agent.start_new_session(title=title)
        return jsonify({
            "success": True,
            "session_id": session_id
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/memory", methods=["GET"])
def get_memory():
    """获取长期记忆内容"""
    agent = get_agent()
    
    try:
        return jsonify({
            "success": True,
            "memory": agent.memory.get_context()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/memory/clear", methods=["POST"])
def clear_memory():
    """清空长期记忆（谨慎使用）"""
    agent = get_agent()
    
    try:
        agent.memory.clear()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/memory/save", methods=["POST"])
def save_to_memory():
    """手动保存内容到长期记忆"""
    agent = get_agent()
    
    try:
        data = request.json
        content_type = data.get("type")  # "table", "metric", "background", "conversation"
        
        if content_type == "table":
            table_name = data.get("table_name")
            columns = data.get("columns", [])
            agent.memory.save_table_schema(table_name, columns)
        elif content_type == "metric":
            metric_name = data.get("metric_name")
            definition = data.get("definition")
            agent.memory.save_metric_definition(metric_name, definition)
        elif content_type == "background":
            item = data.get("item")
            agent.memory.save_business_background(item)
        elif content_type == "conversation":
            content = data.get("content")
            context = data.get("context", "")
            agent.memory.save_conversation_point(content, context)
        else:
            return jsonify({"success": False, "error": "Unknown content type"}), 400
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/interrupt", methods=["POST"])
def interrupt_agent():
    data = request.json
    message = data.get("message", "")
    
    if not message:
        return jsonify({"error": "Empty message"}), 400
    
    agent = get_agent()
    
    try:
        if hasattr(agent, 'cancel_event') and agent.cancel_event:
            agent.cancel_event.set()
        
        agent.session.add_step("user", f"[用户插话] {message}")
        
        return jsonify({
            "success": True,
            "message": "已收到您的反馈"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/skills", methods=["GET"])
def list_skills():
    agent = get_agent()
    
    try:
        skills = agent.skills.list()
        return jsonify({
            "success": True,
            "skills": skills
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/skills/<skill_name>/call", methods=["POST"])
def call_skill(skill_name):
    agent = get_agent()
    data = request.json
    
    try:
        result = agent.skills.call(skill_name, **data)
        return jsonify({
            "success": True,
            "result": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/config", methods=["GET"])
def get_config():
    """获取当前配置信息（不包含敏感信息）"""
    agent = get_agent()
    
    try:
        return jsonify({
            "success": True,
            "config": {
                "llm_model": agent.config.llm_model,
                "llm_base_url": agent.config.llm_base_url,
                "odps_project": agent.config.odps_project,
                "odps_endpoint": agent.config.odps_endpoint,
                "reports_dir": agent.config.reports_dir,
                "memory_path": agent.config.memory_path,
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    try:
        agent = get_agent()

        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": {
                "agent": "ok",
                "memory": "ok",
                "session": "ok",
            }
        }

        return jsonify(health_status), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time(),
        }), 503


@app.route("/health/detailed", methods=["GET"])
def health_check_detailed():
    """Detailed health check with component status."""
    try:
        from gold_miner.circuit_breaker import get_all_circuit_breakers
        from gold_miner.rate_limiter import get_default_limiter, get_chat_limiter

        agent = get_agent()

        # Get circuit breaker status
        circuit_breakers = {}
        for name, breaker in get_all_circuit_breakers().items():
            circuit_breakers[name] = breaker.get_stats()

        # Get rate limiter status
        default_limiter = get_default_limiter()
        chat_limiter = get_chat_limiter()

        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {
                "agent": {
                    "status": "ok",
                    "config": {
                        "llm_model": agent.config.llm_model,
                        "odps_project": agent.config.odps_project,
                    }
                },
                "memory": {
                    "status": "ok",
                    "tables": len(agent.memory.state.table_schemas),
                    "metrics": len(agent.memory.state.metric_definitions),
                },
                "session": {
                    "status": "ok",
                    "current_session": agent.session.get_current_session_id(),
                },
                "circuit_breakers": circuit_breakers,
                "rate_limiters": {
                    "default": default_limiter.is_allowed("health_check")[1],
                    "chat": chat_limiter.is_allowed("health_check")[1],
                },
            }
        }

        return jsonify(health_status), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time(),
        }), 503


@app.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus-style metrics endpoint."""
    try:
        from gold_miner.circuit_breaker import get_all_circuit_breakers

        agent = get_agent()
        lines = []

        # Agent metrics
        lines.append(f'# HELP goldminer_agent_state_size Agent state size')
        lines.append(f'# TYPE goldminer_agent_state_size gauge')
        lines.append(f'goldminer_agent_state_size{{type="results"}} {len(agent.state.results)}')
        lines.append(f'goldminer_agent_state_size{{type="notes"}} {len(agent.state.notes)}')
        lines.append(f'goldminer_agent_state_size{{type="executed_sqls"}} {len(agent.state.executed_sqls)}')

        # Memory metrics
        lines.append(f'# HELP goldminer_memory_size Memory store size')
        lines.append(f'# TYPE goldminer_memory_size gauge')
        lines.append(f'goldminer_memory_size{{type="tables"}} {len(agent.memory.state.table_schemas)}')
        lines.append(f'goldminer_memory_size{{type="metrics"}} {len(agent.memory.state.metric_definitions)}')
        lines.append(f'goldminer_memory_size{{type="background"}} {len(agent.memory.state.business_background)}')

        # Circuit breaker metrics
        for name, breaker in get_all_circuit_breakers().items():
            stats = breaker.get_stats()
            lines.append(f'goldminer_circuit_breaker_state{{name="{name}"}} {1 if stats["state"] == "closed" else 0}')
            lines.append(f'goldminer_circuit_breaker_failures{{name="{name}"}} {stats["failure_count"]}')

        return '\n'.join(lines), 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        return f"# Error generating metrics: {e}", 500


# =============================================================================
# Learning Review Endpoints
# =============================================================================

@app.route("/learnings/review", methods=["POST"])
def trigger_learnings_review():
    """Manually trigger a learnings review and append to memory."""
    try:
        from gold_miner.learning_reviewer import get_learning_reviewer

        reviewer = get_learning_reviewer(
            learnings_dir=".learnings",
        )

        report = reviewer.trigger_review()

        return jsonify({
            "success": True,
            "data": {
                "total_records": report.total_records,
                "pending_high_priority": len(report.pending_high_priority),
                "by_type": report.by_type,
                "by_area": report.by_area,
                "recommendations": report.recommendations,
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/learnings/pending", methods=["GET"])
def get_pending_learnings():
    """Get pending learning records with optional filters."""
    try:
        from gold_miner.learning_reviewer import get_learning_reviewer

        area = request.args.get("area")
        priority = request.args.get("priority")
        limit = int(request.args.get("limit", 10))

        reviewer = get_learning_reviewer(
            learnings_dir=".learnings",
        )

        records = reviewer.get_pending_records(
            area=area,
            priority=priority,
            limit=limit,
        )

        return jsonify({
            "success": True,
            "data": {
                "count": len(records),
                "records": [
                    {
                        "id": r.id,
                        "type": r.type,
                        "area": r.area,
                        "priority": r.priority,
                        "summary": r.summary,
                        "suggested_action": r.suggested_action,
                        "logged_at": r.logged_at.isoformat(),
                    }
                    for r in records
                ]
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/learnings/update/<record_id>", methods=["POST"])
def update_learning_status(record_id):
    """Update status of a learning record."""
    try:
        from gold_miner.learning_reviewer import get_learning_reviewer, ReviewStatus

        data = request.json or {}
        new_status = data.get("status", "pending")
        review_notes = data.get("review_notes", "")

        reviewer = get_learning_reviewer(
            learnings_dir=".learnings",
        )

        success = reviewer.update_record_status(
            record_id,
            ReviewStatus(new_status),
            review_notes,
        )

        if success:
            return jsonify({
                "success": True,
                "message": f"Record {record_id} updated to {new_status}"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Record {record_id} not found"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/learnings/stats", methods=["GET"])
def get_learnings_stats():
    """Get learning review scheduler statistics."""
    try:
        from gold_miner.learning_reviewer import get_learning_reviewer

        reviewer = get_learning_reviewer(
            learnings_dir=".learnings",
        )

        stats = reviewer.get_stats()

        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
