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

_config = Config.from_env()
_config.validate_security()
app.secret_key = _config.session_secret

from gold_miner.agent import SqlAgent
from gold_miner.rate_limiter import RateLimitExceeded, get_chat_limiter, get_default_limiter
from gold_miner.harness import create_harness_agent, HarnessConfig

CONFIG = None
AGENT = None


def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def check_rate_limit(limiter_type="default"):
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
        sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")

        base_agent = SqlAgent(CONFIG, skills_dir, sessions_dir=sessions_dir)

        harness_config = HarnessConfig(
            checkpoint_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints"),
            workspace_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace"),
            learnings_dir=os.path.join(project_root, ".learnings"),
        )
        AGENT = create_harness_agent(base_agent, enable_all=True)

        from gold_miner.services import get_agent_pool
        get_agent_pool(
            config=CONFIG,
            skills_dir=skills_dir,
            sessions_dir=sessions_dir,
        )

    return AGENT


def init_schedulers():
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
        memory_path=os.path.join(project_root, "memory/state.json"),
        review_interval_hours=_config.scheduler_session_review_hours,
        auto_start=True,
    )

    print(f"[App] Schedulers started: review_interval={_config.scheduler_review_interval_hours}h, session_review={_config.scheduler_session_review_hours}h")


init_schedulers()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        rate_info = check_rate_limit("chat")
    except RateLimitExceeded as e:
        return jsonify({"error": str(e)}), 429

    data = request.json
    user_message = data.get("message", "")
    stream = data.get("stream", False)
    new_session = data.get("new_session", False)

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    agent = get_agent()

    if new_session:
        session_id = agent.start_new_session() if hasattr(agent, 'start_new_session') else None
    else:
        session_id = session.get("session_id")

    status_updates = []

    def status_cb(status):
        status_updates.append(status)

    try:
        if stream:
            return Response(
                stream_chat(agent, user_message, session_id, status_cb),
                mimetype="text/event-stream"
            )
        else:
            result = agent.run(
                user_message,
                status_cb=status_cb,
            )
            return jsonify({
                "response": result,
                "status_updates": status_updates
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def stream_chat(agent, user_message, session_id, status_cb):
    """Stream chat response."""
    def generate():
        for update in agent.run(user_message, status_cb=status_cb, stream=True):
            yield f"data: {json.dumps({'update': update})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    return generate()


@app.route("/sessions", methods=["GET"])
def list_sessions():
    try:
        agent = get_agent()
        if hasattr(agent, 'session'):
            sessions = agent.session.list_sessions()
            return jsonify({"success": True, "sessions": sessions})
        return jsonify({"success": True, "sessions": []})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/sessions/new", methods=["POST"])
def new_session():
    try:
        agent = get_agent()
        title = request.json.get("title", "") if request.json else ""
        session_id = agent.start_new_session(title) if hasattr(agent, 'start_new_session') else ""
        return jsonify({"success": True, "session_id": session_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/memory", methods=["GET"])
def get_memory():
    try:
        agent = get_agent()
        if hasattr(agent, 'memory'):
            memory_context = agent.memory.get_context()
            return jsonify({"success": True, "memory": memory_context})
        return jsonify({"success": True, "memory": {}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/memory", methods=["POST"])
def save_memory():
    try:
        data = request.json
        key = data.get("key", "")
        value = data.get("value", "")

        agent = get_agent()
        if hasattr(agent, 'memory'):
            if hasattr(agent.memory, 'save_table_schema'):
                agent.memory.save_table_schema(key, value)
            elif hasattr(agent.memory, 'save_metric_definition'):
                agent.memory.save_metric_definition(key, value)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/memory/clear", methods=["POST"])
def clear_memory():
    try:
        agent = get_agent()
        if hasattr(agent, 'memory') and hasattr(agent.memory, 'clear'):
            agent.memory.clear()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/skills", methods=["GET"])
def list_skills():
    try:
        agent = get_agent()
        if hasattr(agent, 'skills'):
            skills = agent.skills.list()
            return jsonify({"success": True, "skills": skills})
        return jsonify({"success": True, "skills": []})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/config", methods=["GET"])
def get_config():
    try:
        return jsonify({
            "success": True,
            "config": {
                "model": _config.llm_model if hasattr(_config, 'llm_model') else None,
                "max_steps": _config.agent_max_steps if hasattr(_config, 'agent_max_steps') else None,
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/interrupt", methods=["POST"])
def interrupt():
    try:
        data = request.json
        message = data.get("message", "")

        if hasattr(get_agent(), '_cancel_event'):
            agent = get_agent()
            if hasattr(agent, '_cancel_event') and agent._cancel_event:
                agent._cancel_event.set()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "success": True,
        "status": "running",
        "version": "1.0.0"
    })
