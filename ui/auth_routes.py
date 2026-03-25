"""Authentication routes for Flask app."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, request, render_template, redirect, url_for, make_response, current_app

from gold_miner.auth import AuthService, UserStore, require_auth, get_current_user
from gold_miner.auth.feishu_auth import FeishuAuth
from gold_miner.user_data import get_user_data_manager


# Create blueprint
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Global instances (initialized in init_auth)
_auth_service: Optional[AuthService] = None
_feishu_auth: Optional[FeishuAuth] = None
_user_store: Optional[UserStore] = None


def init_auth(app, config):
    """Initialize authentication system.
    
    Args:
        app: Flask application instance
        config: Application configuration
    """
    global _auth_service, _feishu_auth, _user_store
    
    # Initialize user store
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    _user_store = UserStore(data_dir)
    
    # Initialize auth service
    jwt_secret = getattr(config, "jwt_secret", None) or os.getenv("JWT_SECRET", config.session_secret)
    token_expires = getattr(config, "token_expires_hours", 8)
    _auth_service = AuthService(_user_store, jwt_secret, token_expires)
    
    # Initialize Feishu auth
    feishu_app_id = os.getenv("FEISHU_APP_ID", "")
    feishu_app_secret = os.getenv("FEISHU_APP_SECRET", "")
    feishu_redirect_uri = os.getenv("FEISHU_REDIRECT_URI", "")
    
    if feishu_app_id and feishu_app_secret:
        _feishu_auth = FeishuAuth(feishu_app_id, feishu_app_secret, feishu_redirect_uri)
    
    # Store in app for access in decorators
    app.auth_service = _auth_service
    app.feishu_auth = _feishu_auth
    
    # Register blueprint
    app.register_blueprint(auth_bp)
    
    return _auth_service


def _get_client_ip() -> str:
    """Get client IP address."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or ""


def _get_user_agent() -> str:
    """Get user agent string."""
    return request.headers.get('User-Agent', '')


def _set_auth_cookie(response, token: str, expires_hours: int = 8):
    """Set authentication cookie."""
    from datetime import timedelta
    
    max_age = int(timedelta(hours=expires_hours).total_seconds())
    response.set_cookie(
        'session_token',
        token,
        max_age=max_age,
        httponly=True,
        secure=request.is_secure,  # Only HTTPS in production
        samesite='Lax',
    )
    return response


# =============================================================================
# Login Page Routes
# =============================================================================

@auth_bp.route("/login", methods=["GET"])
def login_page():
    """Render login page."""
    # Check if already logged in
    token = request.cookies.get('session_token')
    if token and _auth_service:
        user, _ = _auth_service.verify_token(token)
        if user:
            return redirect('/')
    
    # Check if Feishu auth is configured
    feishu_configured = _feishu_auth is not None
    
    # Generate QR code URL if configured
    qr_code_url = None
    qr_state = None
    if feishu_configured and _feishu_auth:
        try:
            state = _feishu_auth.generate_qr_state()
            # Build redirect URI from current request
            host = request.host  # e.g., localhost:5006
            redirect_uri = f"http://{host}/auth/feishu/callback"
            feishu_login_url = _feishu_auth.get_qr_url(state, redirect_uri)
            # Generate QR code image URL using QR Server API
            qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={feishu_login_url}"
            qr_state = state
        except Exception as e:
            import traceback
            print(f"[Auth] Failed to generate QR code: {e}")
            traceback.print_exc()
    
    return render_template("login.html", 
                          feishu_configured=feishu_configured,
                          qr_code_url=qr_code_url,
                          qr_state=qr_state)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Handle logout."""
    token = request.cookies.get('session_token')
    
    if token and _auth_service:
        _auth_service.logout(token)
    
    response = make_response(redirect('/auth/login'))
    response.delete_cookie('session_token')
    return response


# =============================================================================
# Feishu SSO Routes
# =============================================================================

@auth_bp.route("/feishu/qrcode", methods=["GET"])
def feishu_qrcode():
    """Get Feishu QR code URL for login."""
    if not _feishu_auth:
        return jsonify({
            "success": False,
            "error": "feishu_not_configured",
            "message": "Feishu SSO is not configured",
        }), 503
    
    state = _feishu_auth.generate_qr_state()
    qr_url = _feishu_auth.get_qr_url(state)
    
    return jsonify({
        "success": True,
        "data": {
            "qr_url": qr_url,
            "state": state,
        },
    })


@auth_bp.route("/feishu/callback", methods=["GET"])
def feishu_callback():
    """Handle Feishu OAuth callback."""
    code = request.args.get("code")
    state = request.args.get("state")
    
    if not code or not state:
        return render_template("auth_error.html", error="Missing authorization code or state"), 400
    
    if not _feishu_auth or not _auth_service:
        return render_template("auth_error.html", error="Authentication service not available"), 503
    
    # Verify state
    if not _feishu_auth.verify_state(state):
        return render_template("auth_error.html", error="Invalid or expired state"), 400
    
    _feishu_auth.mark_state_used(state)
    
    # Exchange code for access token
    access_token, error = _feishu_auth.get_access_token_by_code(code)
    if error:
        return render_template("auth_error.html", error=f"Failed to get access token: {error}"), 400
    
    # Get user info
    feishu_user_info, error = _feishu_auth.get_user_info(access_token)
    if error:
        return render_template("auth_error.html", error=f"Failed to get user info: {error}"), 400
    
    # Authenticate user
    ip_address = _get_client_ip()
    user_agent = _get_user_agent()
    
    user, token, error = _auth_service.authenticate_feishu_user(
        feishu_user_info,
        ip_address,
        user_agent,
    )
    
    if not user or not token:
        return render_template("auth_error.html", error=error or "Authentication failed"), 400
    
    # Create user data directories
    user_data_manager = get_user_data_manager()
    user_data_manager.create_user_directories(user.id)
    
    # Redirect to home with token in cookie
    response = make_response(redirect('/'))
    _set_auth_cookie(response, token)
    return response


@auth_bp.route("/feishu/poll", methods=["GET"])
def feishu_poll():
    """Poll for login status (for AJAX polling approach)."""
    # This endpoint would be used with a polling-based approach
    # For now, we use the callback approach
    return jsonify({
        "success": False,
        "error": "not_implemented",
        "message": "Polling is not implemented, use callback approach",
    }), 501


# =============================================================================
# API Routes
# =============================================================================

@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_current_user_info():
    """Get current logged-in user information."""
    user = get_current_user()
    
    return jsonify({
        "success": True,
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar": user.avatar,
            "department": user.department_name,
            "job_title": user.job_title,
            "role": user.role,
            "permissions": user.permissions if user.permissions else [],
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
        },
    })


@auth_bp.route("/refresh", methods=["POST"])
@require_auth
def refresh_token():
    """Refresh access token."""
    from flask import g
    
    old_token = g.current_token
    new_token, error = _auth_service.refresh_token(old_token)
    
    if not new_token:
        return jsonify({
            "success": False,
            "error": "refresh_failed",
            "message": error or "Failed to refresh token",
        }), 401
    
    response = jsonify({
        "success": True,
        "data": {
            "token": new_token,
        },
    })
    
    _set_auth_cookie(response, new_token)
    return response


@auth_bp.route("/status", methods=["GET"])
def auth_status():
    """Check authentication status."""
    token = request.cookies.get('session_token')
    
    if not token or not _auth_service:
        return jsonify({
            "success": True,
            "data": {
                "authenticated": False,
            },
        })
    
    user, error = _auth_service.verify_token(token)
    
    if not user:
        return jsonify({
            "success": True,
            "data": {
                "authenticated": False,
                "error": error,
            },
        })
    
    return jsonify({
        "success": True,
        "data": {
            "authenticated": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role,
            },
        },
    })


@auth_bp.route("/login/password", methods=["POST"])
def login_password():
    """使用用户名密码登录"""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "success": False,
            "error": "missing_credentials",
            "message": "用户名和密码不能为空",
        }), 400

    if not _auth_service:
        return jsonify({
            "success": False,
            "error": "service_not_available",
            "message": "认证服务不可用",
        }), 503

    ip_address = _get_client_ip()
    user_agent = _get_user_agent()

    user, token, error = _auth_service.authenticate_by_password(
        username, password, ip_address, user_agent
    )

    if not user or not token:
        return jsonify({
            "success": False,
            "error": "invalid_credentials",
            "message": error or "用户名或密码错误",
        }), 401

    # 创建用户数据目录
    from gold_miner.user_data import get_user_data_manager
    user_data_manager = get_user_data_manager()
    user_data_manager.create_user_directories(user.id)

    response = jsonify({
        "success": True,
        "data": {
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role,
            },
        },
    })

    _set_auth_cookie(response, token)
    return response


@auth_bp.route("/register", methods=["POST"])
def register():
    """注册新用户"""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    name = data.get("name", "").strip()

    if not username or not password:
        return jsonify({
            "success": False,
            "error": "missing_fields",
            "message": "用户名和密码不能为空",
        }), 400

    if len(username) < 3:
        return jsonify({
            "success": False,
            "error": "invalid_username",
            "message": "用户名至少需要3个字符",
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "error": "invalid_password",
            "message": "密码至少需要6个字符",
        }), 400

    if not _auth_service:
        return jsonify({
            "success": False,
            "error": "service_not_available",
            "message": "认证服务不可用",
        }), 503

    user, error = _auth_service.register_user(username, password, name)

    if not user:
        return jsonify({
            "success": False,
            "error": "registration_failed",
            "message": error or "注册失败",
        }), 400

    return jsonify({
        "success": True,
        "data": {
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "role": user.role,
            },
        },
        "message": "注册成功，请登录",
    })
