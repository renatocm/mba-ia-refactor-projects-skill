from flask import Blueprint,request,jsonify
from database import db
from models.user import User
from models.task import Task
from services import user_service
from auth import auth_required,issue_token
from utils.validation import validate_user
from sqlalchemy.orm import selectinload
user_bp=Blueprint("users",__name__)
@user_bp.route("/users",methods=["GET"])
@auth_required({"admin","manager"})
def get_users():
    users=User.query.options(selectinload(User.tasks)).all(); return jsonify([{**u.to_dict(),"task_count":len(u.tasks)} for u in users]),200
@user_bp.route("/users/<int:user_id>",methods=["GET"])
@auth_required()
def get_user(user_id):
    u=user_service.get(user_id)
    if not u:return jsonify(error="Usuário não encontrado"),404
    return jsonify({**u.to_dict(),"tasks":[t.to_dict() for t in u.tasks]}),200
@user_bp.route("/users",methods=["POST"])
def create_user():
    data=request.get_json(silent=True) or {}
    # Public registration always creates a regular user; elevation requires an admin.
    data.pop("role",None); data.pop("active",None)
    try:return jsonify(user_service.create(data).to_dict()),201
    except KeyError as e:return jsonify(error=str(e)),409
    except (ValueError,TypeError) as e:return jsonify(error=str(e)),400
@user_bp.route("/users/<int:user_id>",methods=["PUT"])
@auth_required()
def update_user(user_id):
    u=user_service.get(user_id)
    if not u:return jsonify(error="Usuário não encontrado"),404
    from auth import current_user
    actor=current_user()
    if actor.id != user_id and actor.role != "admin": return jsonify(error="Acesso negado"),403
    data=request.get_json(silent=True) or {}
    if "role" in data or "active" in data:
        from auth import current_user
        if current_user().role!="admin":return jsonify(error="Acesso negado"),403
    try:return jsonify(user_service.update(u,data).to_dict()),200
    except (ValueError,TypeError) as e:db.session.rollback();return jsonify(error=str(e)),400
@user_bp.route("/users/<int:user_id>",methods=["DELETE"])
@auth_required({"admin"})
def delete_user(user_id):
    u=user_service.get(user_id)
    if not u:return jsonify(error="Usuário não encontrado"),404
    db.session.delete(u);db.session.commit();return jsonify(message="Usuário deletado com sucesso"),200
@user_bp.route("/users/<int:user_id>/tasks",methods=["GET"])
@auth_required()
def get_user_tasks(user_id):
    if not user_service.get(user_id):return jsonify(error="Usuário não encontrado"),404
    return jsonify([t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]),200
@user_bp.route("/login",methods=["POST"])
def login():
    data=request.get_json(silent=True) or {}; u=User.query.filter_by(email=data.get("email","").lower()).first()
    if not u or not u.check_password(data.get("password","")):return jsonify(error="Credenciais inválidas"),401
    if not u.active:return jsonify(error="Usuário inativo"),403
    return jsonify(message="Login realizado com sucesso",user=u.to_dict(),token=issue_token(u)),200
