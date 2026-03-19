import json
import os
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
app.secret_key = os.getenv("SESSION_SECRET", "gold-miner-secret-key")

from gold_miner.agent import SqlAgent
from gold_miner.config import Config

CONFIG = None
AGENT = None


def get_agent():
    global AGENT, CONFIG
    if AGENT is None:
        CONFIG = Config.from_env()
        CONFIG.validate()
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skills_dir = os.path.join(project_root, "skills")
        AGENT = SqlAgent(CONFIG, skills_dir)
    
    return AGENT


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    stream = data.get("stream", False)
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    agent = get_agent()
    
    def generate():
        try:
            agent.memory.add_step("user", user_message)
            yield f"data: {json.dumps({'type': 'message', 'role': 'user', 'content': user_message})}\n\n"
            
            def status_callback(status):
                if isinstance(status, dict):
                    yield f"data: {json.dumps(status)}\n\n"
                elif status == "starting":
                    yield f"data: {json.dumps({'type': 'status', 'content': '开始处理...'})}\n\n"
                elif status == "done":
                    yield f"data: {json.dumps({'type': 'status', 'content': '完成'})}\n\n"
            
            report_path = agent.run(user_message, status_cb=status_callback)
            
            response_text = ""
            if report_path and os.path.exists(report_path):
                with open(report_path, "r", encoding="utf-8") as f:
                    response_text = f.read()
            else:
                response_text = str(report_path) if report_path else "任务完成"
            
            agent.memory.add_step("assistant", response_text)
            agent.memory._save()
            
            yield f"data: {json.dumps({'type': 'message', 'role': 'assistant', 'content': response_text})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    if stream:
        return Response(generate(), mimetype='text/event-stream')
    
    # Non-streaming mode
    try:
        agent.memory.add_step("user", user_message)
        
        report_path = agent.run(user_message)
        
        response_text = ""
        if report_path and os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                response_text = f.read()
        else:
            response_text = str(report_path) if report_path else "任务完成"
        
        agent.memory.add_step("assistant", response_text)
        agent.memory._save()
        
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


@app.route("/memory", methods=["GET"])
def get_memory():
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
    agent = get_agent()
    
    try:
        agent.memory.clear()
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
        
        agent.memory.add_step("user", f"[用户插话] {message}")
        
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
    get_agent()
    
    return jsonify({
        "success": True,
        "config": {
            "llm_model": CONFIG.llm_model,
            "llm_base_url": CONFIG.llm_base_url,
            "odps_project": CONFIG.odps_project,
            "max_steps": CONFIG.agent_max_steps,
        }
    })


@app.route("/learnings", methods=["GET"])
def get_learnings():
    learnings_dir = Path(".learnings")
    
    if not learnings_dir.exists():
        return jsonify({
            "success": True,
            "learnings": [],
            "errors": [],
            "features": []
        })
    
    def read_file(filename):
        path = learnings_dir / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""
    
    return jsonify({
        "success": True,
        "learnings": read_file("LEARNINGS.md"),
        "errors": read_file("ERRORS.md"),
        "features": read_file("FEATURE_REQUESTS.md")
    })


@app.route("/api/tables", methods=["GET"])
def get_tables():
    """获取知识库中所有可用的表"""
    try:
        project_root = Path(__file__).parent.parent
        tables_dir = project_root / "knowledge" / "tables"
        
        tables = []
        if tables_dir.exists():
            for yaml_file in tables_dir.glob("*.yaml"):
                try:
                    import yaml
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        table_info = yaml.safe_load(f)
                        if table_info:
                            tables.append({
                                "name": table_info.get("表名", yaml_file.stem),
                                "description": table_info.get("描述", ""),
                                "file": yaml_file.name
                            })
                except Exception as e:
                    print(f"Error loading table {yaml_file}: {e}")
        
        return jsonify({
            "success": True,
            "tables": tables
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/skills", methods=["GET"])
def get_skills():
    """获取所有可用的技能"""
    agent = get_agent()
    
    try:
        # agent.skills.list() 返回的是字典列表
        skills_list = agent.skills.list()
        
        return jsonify({
            "success": True,
            "skills": skills_list
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
