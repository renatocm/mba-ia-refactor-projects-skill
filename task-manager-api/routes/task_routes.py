from flask import Blueprint, request, jsonify
from auth import auth_required
from services import task_service


task_bp=Blueprint("tasks",__name__)


@task_bp.route("/tasks",methods=["GET"])
@auth_required()
def get_tasks():
    return jsonify(task_service.list_tasks()), 200


@task_bp.route("/tasks/<int:task_id>",methods=["GET"])
@auth_required()
def get_task(task_id):
    return jsonify(task_service.get_task(task_id)), 200


@task_bp.route("/tasks",methods=["POST"])
@auth_required({"admin","manager"})
def create_task():
    return jsonify(task_service.create(request.get_json(silent=True))), 201


@task_bp.route("/tasks/<int:task_id>",methods=["PUT"])
@auth_required({"admin","manager"})
def update_task(task_id):
    return jsonify(task_service.update(task_id, request.get_json(silent=True))), 200


@task_bp.route("/tasks/<int:task_id>",methods=["DELETE"])
@auth_required({"admin","manager"})
def delete_task(task_id):
    task_service.delete(task_id)
    return jsonify(message="Task deletada com sucesso"), 200


@task_bp.route("/tasks/search",methods=["GET"])
@auth_required()
def search_tasks():
    return jsonify(task_service.search(
        q=request.args.get("q", ""),
        status=request.args.get("status"),
        priority=request.args.get("priority"),
    )), 200


@task_bp.route("/tasks/stats",methods=["GET"])
@auth_required()
def stats():
    return jsonify(task_service.stats()), 200
