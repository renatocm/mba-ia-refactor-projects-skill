from flask import Blueprint, request, jsonify
from auth import auth_required, current_user, issue_token
from services import user_service


user_bp=Blueprint("users",__name__)


@user_bp.route("/users",methods=["GET"])
@auth_required({"admin","manager"})
def get_users():
    return jsonify(user_service.list_users()), 200


@user_bp.route("/users/<int:user_id>",methods=["GET"])
@auth_required()
def get_user(user_id):
    return jsonify(user_service.get(user_id)), 200


@user_bp.route("/users",methods=["POST"])
def create_user():
    return jsonify(user_service.create(request.get_json(silent=True) or {})), 201


@user_bp.route("/users/<int:user_id>",methods=["PUT"])
@auth_required()
def update_user(user_id):
    return jsonify(user_service.update(
        user_id, request.get_json(silent=True) or {}, current_user()
    )), 200


@user_bp.route("/users/<int:user_id>",methods=["DELETE"])
@auth_required({"admin"})
def delete_user(user_id):
    user_service.delete(user_id)
    return jsonify(message="Usuário deletado com sucesso"), 200


@user_bp.route("/users/<int:user_id>/tasks",methods=["GET"])
@auth_required()
def get_user_tasks(user_id):
    return jsonify(user_service.tasks(user_id)), 200


@user_bp.route("/login",methods=["POST"])
def login():
    user = user_service.authenticate(request.get_json(silent=True) or {})
    return jsonify(message="Login realizado com sucesso", user=user.to_dict(), token=issue_token(user)), 200
