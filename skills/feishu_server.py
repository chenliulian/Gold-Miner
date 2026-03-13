import json
import os
import threading
from typing import Any, Callable, Dict, Optional

from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()


app = Flask(__name__)

MESSAGE_HANDLER: Optional[Callable[[str, Dict], Any]] = None


@app.route("/feishu/webhook", methods=["POST"])
def feishu_webhook():
    data = request.json

    msg_type = data.get("type")

    if msg_type == "url_verification":
        return jsonify({
            "challenge": data.get("challenge")
        })

    if msg_type == "event_callback":
        event = data.get("event", {})
        event_type = event.get("type")

        if event_type == "im.message":
            message = event.get("message", {})
            msg_content = message.get("content", {})
            text = ""

            if isinstance(msg_content, str):
                try:
                    text = json.loads(msg_content).get("text", "")
                except:
                    text = msg_content

            sender_id = event.get("sender", {}).get("sender_id", {}).get("open_id", "")
            chat_id = message.get("chat_id", "")

            if text and MESSAGE_HANDLER:
                try:
                    result = MESSAGE_HANDLER(text, {
                        "sender_id": sender_id,
                        "chat_id": chat_id,
                        "message_id": message.get("message_id"),
                        "msg_type": message.get("msg_type"),
                    })
                    return jsonify({"code": 0, "msg": "success"})
                except Exception as e:
                    return jsonify({"code": 500, "msg": str(e)})

    return jsonify({"code": 0, "msg": "no action taken"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


def start_server(port: int = 18789, debug: bool = False):
    app.run(host="0.0.0.0", port=port, debug=debug)


def start_background(port: int = 18789, debug: bool = False):
    thread = threading.Thread(target=start_server, args=(port, debug), daemon=True)
    thread.start()
    return thread


def set_message_handler(handler: Callable[[str, Dict], Any]):
    global MESSAGE_HANDLER
    MESSAGE_HANDLER = handler


def run(
    port: int = 18789,
    message_handler: Optional[Callable[[str, Dict], Any]] = None,
) -> Dict[str, Any]:
    if message_handler:
        set_message_handler(message_handler)

    print(f"🚀 飞书 Webhook 服务器启动中...")
    print(f"📍 回调地址: http://<your-server>:{port}/feishu/webhook")
    print(f"   请在飞书开放平台配置此回调地址")
    print(f"⏹️  按 Ctrl+C 停止服务器")

    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    except KeyboardInterrupt:
        return {"status": "stopped", "message": "Server stopped"}


SKILL = {
    "name": "feishu_server",
    "description": "启动飞书消息接收服务器。需要配置飞书开放平台的回调地址为: http://<your-server>:18789/feishu/webhook",
    "inputs": {
        "port": "int (可选) - 服务器端口，默认 18789",
        "message_handler": "func (可选) - 消息处理函数",
    },
    "run": run,
    "start_background": start_background,
    "set_handler": set_message_handler,
}
