from typing import Any, Dict, Optional
import requests
import os
import time


TENANT_ACCESS_TOKEN_CACHE = {"token": None, "expires_at": 0}
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"


def _get_tenant_access_token(app_id: str, app_secret: str) -> Optional[str]:
    global TENANT_ACCESS_TOKEN_CACHE

    if TENANT_ACCESS_TOKEN_CACHE["token"] and time.time() < TENANT_ACCESS_TOKEN_CACHE["expires_at"]:
        return TENANT_ACCESS_TOKEN_CACHE["token"]

    url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
    payload = {"app_id": app_id, "app_secret": app_secret}

    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()

        if result.get("code") == 0:
            TENANT_ACCESS_TOKEN_CACHE["token"] = result["tenant_access_token"]
            TENANT_ACCESS_TOKEN_CACHE["expires_at"] = time.time() + result.get("expire", 7200) - 60
            return result["tenant_access_token"]
        else:
            print(f"Failed to get tenant access token: {result.get('msg')}")
            return None
    except Exception as e:
        print(f"Error getting tenant access token: {e}")
        return None


def _send_message_via_app(
    message: str,
    receive_id: str,
    receive_id_type: str = "open_id",
    msg_type: str = "text",
) -> Dict[str, Any]:
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    if not app_id or not app_secret:
        return {
            "status": "error",
            "message": "FEISHU_APP_ID or FEISHU_APP_SECRET not configured",
        }

    token = _get_tenant_access_token(app_id, app_secret)
    if not token:
        return {"status": "error", "message": "Failed to get access token"}

    url = f"{FEISHU_API_BASE}/im/v1/messages"
    params = {"receive_id_type": receive_id_type}

    payload = {
        "receive_id": receive_id,
        "msg_type": msg_type,
        "content": '{"text": "' + message.replace('"', '\\"') + '"}',
    }

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(url, params=params, json=payload, headers=headers, timeout=10)
        result = response.json()

        if result.get("code") == 0:
            return {"status": "success", "message": "Message sent successfully", "response": result}
        else:
            return {"status": "error", "message": f"Feishu API error: {result.get('msg')}", "response": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_message(
    message: str,
    webhook_url: Optional[str] = None,
    msg_type: str = "text",
    at_all: bool = False,
    receive_id: Optional[str] = None,
    receive_id_type: str = "open_id",
) -> Dict[str, Any]:
    """
    发送消息到飞书群或用户

    参数:
        message: 消息内容
        webhook_url: 飞书机器人 Webhook 地址（兼容旧版）
        msg_type: 消息类型，'text' 或 'markdown'
        at_all: 是否 @所有人（仅对 webhook 有效）
        receive_id: 接收者 ID (open_id/user_id/union_id/chat_id)
        receive_id_type: 接收者 ID 类型，默认 'open_id'，可设为 'chat_id'
    """
    if receive_id:
        return _send_message_via_app(message, receive_id, receive_id_type=receive_id_type, msg_type=msg_type)

    # 如果没有指定 receive_id，尝试使用默认群 ID
    default_chat_id = os.getenv("FEISHU_DEFAULT_CHAT_ID")
    if default_chat_id:
        return _send_message_via_app(message, default_chat_id, receive_id_type="chat_id", msg_type=msg_type)

    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")

    if not webhook_url:
        return {
            "status": "error",
            "message": "FEISHU_WEBHOOK_URL or receive_id not configured",
        }

    if msg_type == "markdown":
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "GoldMiner 通知"
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": message
                    }
                ]
            }
        }
    else:
        payload = {
            "msg_type": "text",
            "content": {
                "text": message + ("\n\n@all" if at_all else "")
            }
        }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        result = response.json()

        if result.get("code") == 0:
            return {
                "status": "success",
                "message": "Message sent to Feishu successfully",
                "response": result,
            }
        else:
            return {
                "status": "error",
                "message": f"Feishu API error: {result.get('msg', 'Unknown error')}",
                "response": result,
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


def send_report(
    title: str,
    summary: str,
    details: str = "",
    webhook_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    发送数据分析报告卡片到飞书群

    参数:
        title: 报告标题
        summary: 报告摘要
        details: 详细报告内容（支持 Markdown）
        webhook_url: 飞书机器人 Webhook 地址
    """
    webhook_url = webhook_url or os.getenv("FEISHU_WEBHOOK_URL")

    if not webhook_url:
        return {
            "status": "error",
            "message": "FEISHU_WEBHOOK_URL not configured",
        }

    markdown_content = f"**{title}**\n\n{summary}"
    if details:
        markdown_content += f"\n\n---\n{details}"

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📊 {title}"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": markdown_content
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "查看详情"
                            },
                            "type": "primary",
                            "url": "https://github.com/gold-miner"
                        }
                    ]
                }
            ]
        }
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        result = response.json()

        if result.get("code") == 0:
            return {
                "status": "success",
                "message": "Report sent to Feishu successfully",
            }
        else:
            return {
                "status": "error",
                "message": f"Feishu API error: {result.get('msg', 'Unknown error')}",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


def check_webhook(webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """
    检查飞书 Webhook 配置是否正确

    参数:
        webhook_url: 飞书机器人 Webhook 地址
    """
    webhook_url = webhook_url or os.getenv("FEISHU_WEBHOOK_URL")

    if not webhook_url:
        return {
            "status": "error",
            "message": "FEISHU_WEBHOOK_URL not configured",
            "configured": False,
        }

    test_message = "🔔 GoldMiner 连接测试消息"
    result = send_message(test_message, webhook_url)

    return {
        "status": result["status"],
        "message": result.get("message", ""),
        "webhook_configured": True,
        "webhook_url": webhook_url[:20] + "..." if len(webhook_url) > 20 else webhook_url,
    }


SKILL = {
    "name": "feishu_notify",
    "description": "发送消息到飞书群或用户。支持飞书应用机器人(Webhook)或自定义机器人(App ID/Secret)。可用于发送分析报告和通知。",
    "inputs": {
        "message": "str (必需) - 消息内容",
        "receive_id": "str (可选) - 飞书应用时，接收者ID (open_id/user_id/union_id/chat_id)",
        "webhook_url": "str (可选) - Webhook 地址，默认从环境变量读取",
        "msg_type": "str (可选) - 消息类型: 'text' 或 'markdown'，默认 'text'",
        "at_all": "bool (可选) - 是否 @所有人，默认 False",
    },
    "run": send_message,
    "send_report": send_report,
    "check_webhook": check_webhook,
}
