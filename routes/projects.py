# routes/projects.py
from flask import Blueprint, request, jsonify
from core.projects import project_manager, ProjectError

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("/api/projects", methods=["GET"])
def list_projects():
    return jsonify(project_manager.list_projects())


@projects_bp.route("/api/projects", methods=["POST"])
def create_project():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "zprava": "Očekávána JSON data."}), 400
    try:
        project = project_manager.create_project(
            data.get("name"),
            data.get("description", ""),
            data.get("instructions", "")
        )
        return jsonify({"status": "ok", "project": project}), 201
    except ProjectError as exc:
        return jsonify({"status": "error", "zprava": str(exc)}), 400


@projects_bp.route("/api/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    try:
        return jsonify(project_manager.get_project(project_id))
    except ProjectError as exc:
        return jsonify({"status": "error", "zprava": str(exc)}), 404


@projects_bp.route("/api/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "zprava": "Očekávána JSON data."}), 400
    try:
        project = project_manager.update_project(
            project_id,
            data.get("name"),
            data.get("description"),
            data.get("instructions")
        )
        return jsonify({"status": "ok", "project": project})
    except ProjectError as exc:
        status = 404 if "nebyl nalezen" in str(exc) else 400
        return jsonify({"status": "error", "zprava": str(exc)}), status


@projects_bp.route("/api/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    try:
        project_manager.delete_project(project_id)
        return jsonify({"status": "ok"})
    except ProjectError as exc:
        return jsonify({"status": "error", "zprava": str(exc)}), 404


@projects_bp.route("/api/projects/<int:project_id>/folders", methods=["POST"])
def add_project_folder(project_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "zprava": "Očekávána JSON data."}), 400
    try:
        project = project_manager.add_folder(
            project_id, data.get("path"), data.get("access")
        )
        return jsonify({"status": "ok", "project": project}), 201
    except ProjectError as exc:
        status = 404 if "Projekt nebyl nalezen" in str(exc) else 400
        return jsonify({"status": "error", "zprava": str(exc)}), status


@projects_bp.route("/api/projects/<int:project_id>/folders", methods=["DELETE"])
def remove_project_folder(project_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "zprava": "Očekávána JSON data."}), 400
    try:
        project = project_manager.remove_folder(project_id, data.get("path"))
        return jsonify({"status": "ok", "project": project})
    except ProjectError as exc:
        status = 404 if "nebyla nalezena" in str(exc) or "nebyl nalezen" in str(exc) else 400
        return jsonify({"status": "error", "zprava": str(exc)}), status
