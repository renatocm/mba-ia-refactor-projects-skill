from flask import Blueprint,request,jsonify
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from auth import auth_required
from utils.validation import validate_category
from sqlalchemy import func
from utils.time import utc_now
from datetime import timedelta
report_bp=Blueprint("reports",__name__)
@report_bp.route("/reports/summary")
@auth_required({"admin","manager"})
def summary_report():
    tasks=Task.query.all(); users=User.query.all(); cats=Category.query.count()
    by_status={s:sum(t.status==s for t in tasks) for s in ("pending","in_progress","done","cancelled")}
    by_priority={str(p):sum(t.priority==p for t in tasks) for p in range(1,6)}
    overdue=[{"id":t.id,"title":t.title,"due_date":t.due_date.isoformat()} for t in tasks if t.to_dict()["overdue"]]
    stats=[]
    for u in users:
        own=[t for t in tasks if t.user_id==u.id]; done=sum(t.status=="done" for t in own); stats.append({"user_id":u.id,"user_name":u.name,"total_tasks":len(own),"completed_tasks":done,"completion_rate":round(done/len(own)*100,2) if own else 0})
    seven_days_ago=utc_now()-timedelta(days=7)
    recent_created=sum(bool(t.created_at and (t.created_at.replace(tzinfo=t.created_at.tzinfo or utc_now().tzinfo) >= seven_days_ago)) for t in tasks)
    recent_done=sum(bool(t.status=="done" and t.updated_at and (t.updated_at.replace(tzinfo=t.updated_at.tzinfo or utc_now().tzinfo) >= seven_days_ago)) for t in tasks)
    priority_labels={"critical":by_priority["1"],"high":by_priority["2"],"medium":by_priority["3"],"low":by_priority["4"],"minimal":by_priority["5"]}
    return jsonify({"generated_at":utc_now().isoformat(),"overview":{"total_tasks":len(tasks),"total_users":len(users),"total_categories":cats},"tasks_by_status":by_status,"tasks_by_priority":priority_labels,"overdue":{"count":len(overdue),"tasks":overdue},"recent_activity":{"tasks_created_last_7_days":recent_created,"tasks_completed_last_7_days":recent_done},"user_productivity":stats}),200
@report_bp.route("/reports/user/<int:user_id>")
@auth_required()
def user_report(user_id):
    u=db.session.get(User,user_id)
    if not u:return jsonify(error="Usuário não encontrado"),404
    ts=Task.query.filter_by(user_id=user_id).all(); done=sum(t.status=="done" for t in ts)
    return jsonify({"user":{"id":u.id,"name":u.name,"email":u.email},"statistics":{"total_tasks":len(ts),"done":done,"pending":sum(t.status=="pending" for t in ts),"in_progress":sum(t.status=="in_progress" for t in ts),"cancelled":sum(t.status=="cancelled" for t in ts),"overdue":sum(t.to_dict()["overdue"] for t in ts),"high_priority":sum(t.priority<=2 for t in ts),"completion_rate":round(done/len(ts)*100,2) if ts else 0}}),200
@report_bp.route("/categories",methods=["GET"])
@auth_required()
def get_categories():
    rows=db.session.query(Category,func.count(Task.id)).outerjoin(Task).group_by(Category.id).all(); return jsonify([{**c.to_dict(),"task_count":n} for c,n in rows]),200
@report_bp.route("/categories",methods=["POST"])
@auth_required({"admin","manager"})
def create_category():
    try:
        d=request.get_json(silent=True);validate_category(d); c=Category(name=d["name"],description=d.get("description",""),color=d.get("color","#000000"));db.session.add(c);db.session.commit();return jsonify(c.to_dict()),201
    except (ValueError,TypeError) as e:db.session.rollback();return jsonify(error=str(e)),400
@report_bp.route("/categories/<int:cat_id>",methods=["PUT"])
@auth_required({"admin","manager"})
def update_category(cat_id):
    c=db.session.get(Category,cat_id)
    if not c:return jsonify(error="Categoria não encontrada"),404
    try:
        d=request.get_json(silent=True) or {};validate_category(d,True)
        for k in ("name","description","color"):
            if k in d:setattr(c,k,d[k])
        db.session.commit();return jsonify(c.to_dict()),200
    except (ValueError,TypeError) as e:db.session.rollback();return jsonify(error=str(e)),400
@report_bp.route("/categories/<int:cat_id>",methods=["DELETE"])
@auth_required({"admin"})
def delete_category(cat_id):
    c=db.session.get(Category,cat_id)
    if not c:return jsonify(error="Categoria não encontrada"),404
    db.session.delete(c);db.session.commit();return jsonify(message="Categoria deletada"),200
