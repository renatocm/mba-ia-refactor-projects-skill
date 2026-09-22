from flask import Blueprint,request,jsonify
from database import db
from models.task import Task
from services import task_service
from utils.validation import validate_task
from auth import auth_required
from sqlalchemy import or_
task_bp=Blueprint("tasks",__name__)
def err(e):
    db.session.rollback(); return jsonify(error=str(e)),400
@task_bp.route("/tasks",methods=["GET"])
@auth_required()
def get_tasks(): return jsonify([t.to_dict() for t in task_service.list_tasks()]),200
@task_bp.route("/tasks/<int:task_id>",methods=["GET"])
@auth_required()
def get_task(task_id):
    t=task_service.get_task(task_id); return (jsonify(t.to_dict()),200) if t else (jsonify(error="Task não encontrada"),404)
@task_bp.route("/tasks",methods=["POST"])
@auth_required({"admin","manager"})
def create_task():
    try: return jsonify(task_service.create(request.get_json(silent=True)).to_dict()),201
    except LookupError as e: return jsonify(error=str(e)),404
    except (ValueError,TypeError) as e: return err(e)
@task_bp.route("/tasks/<int:task_id>",methods=["PUT"])
@auth_required({"admin","manager"})
def update_task(task_id):
    t=task_service.get_task(task_id)
    if not t:return jsonify(error="Task não encontrada"),404
    try:return jsonify(task_service.update(t,request.get_json(silent=True)).to_dict()),200
    except LookupError as e:return jsonify(error=str(e)),404
    except (ValueError,TypeError) as e:return err(e)
@task_bp.route("/tasks/<int:task_id>",methods=["DELETE"])
@auth_required({"admin","manager"})
def delete_task(task_id):
    t=task_service.get_task(task_id)
    if not t:return jsonify(error="Task não encontrada"),404
    db.session.delete(t);db.session.commit();return jsonify(message="Task deletada com sucesso"),200
@task_bp.route("/tasks/search",methods=["GET"])
@auth_required()
def search_tasks():
    q=request.args.get("q",""); query=Task.query
    if q: query=query.filter(or_(Task.title.ilike(f"%{q}%"),Task.description.ilike(f"%{q}%")))
    if request.args.get("status"): query=query.filter_by(status=request.args["status"])
    if request.args.get("priority"):
        try: query=query.filter_by(priority=int(request.args["priority"]))
        except ValueError:return jsonify(error="Prioridade inválida"),400
    return jsonify([t.to_dict() for t in query.all()]),200
@task_bp.route("/tasks/stats",methods=["GET"])
@auth_required()
def stats():
    tasks=Task.query.all(); return jsonify({"total":len(tasks),"pending":sum(t.status=="pending" for t in tasks),"in_progress":sum(t.status=="in_progress" for t in tasks),"done":sum(t.status=="done" for t in tasks),"cancelled":sum(t.status=="cancelled" for t in tasks),"overdue":sum(t.to_dict()["overdue"] for t in tasks)}),200
