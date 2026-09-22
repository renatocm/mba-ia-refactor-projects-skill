from functools import wraps
from flask import request, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from models.user import User
from database import db

def issue_token(user):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"]).dumps({"user_id":user.id,"role":user.role})

def current_user():
    token=request.headers.get("Authorization","")
    if not token.startswith("Bearer "): return None
    try:
        data=URLSafeTimedSerializer(current_app.config["SECRET_KEY"]).loads(token[7:], max_age=current_app.config["AUTH_TOKEN_TTL"])
    except (BadSignature, SignatureExpired): return None
    return db.session.get(User, data.get("user_id"))

def auth_required(roles=None):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args,**kwargs):
            user=current_user()
            if not user or not user.active: return jsonify(error="Autenticação necessária"),401
            if roles and user.role not in roles: return jsonify(error="Acesso negado"),403
            return fn(*args,**kwargs)
        return wrapped
    return decorator
