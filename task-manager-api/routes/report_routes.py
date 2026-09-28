from flask import Blueprint, request, jsonify
from auth import auth_required
from services import category_service, report_service


report_bp=Blueprint("reports",__name__)


@report_bp.route("/reports/summary")
@auth_required({"admin","manager"})
def summary_report():
    return jsonify(report_service.summary_report()), 200


@report_bp.route("/reports/user/<int:user_id>")
@auth_required()
def user_report(user_id):
    return jsonify(report_service.user_report(user_id)), 200


@report_bp.route("/categories",methods=["GET"])
@auth_required()
def get_categories():
    return jsonify(category_service.list_categories()), 200


@report_bp.route("/categories",methods=["POST"])
@auth_required({"admin","manager"})
def create_category():
    return jsonify(category_service.create(request.get_json(silent=True))), 201


@report_bp.route("/categories/<int:cat_id>",methods=["PUT"])
@auth_required({"admin","manager"})
def update_category(cat_id):
    return jsonify(category_service.update(cat_id, request.get_json(silent=True) or {})), 200


@report_bp.route("/categories/<int:cat_id>",methods=["DELETE"])
@auth_required({"admin"})
def delete_category(cat_id):
    category_service.delete(cat_id)
    return jsonify(message="Categoria deletada"), 200
