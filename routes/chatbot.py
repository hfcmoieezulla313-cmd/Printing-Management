from flask import Blueprint, request, jsonify, session

from services.chatbot_service import handle_chat_message, get_quick_suggestions
from utils import current_user

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chat")


@chatbot_bp.route("", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    session_id = data.get("session_id") or session.get("chat_session_id")

    try:
        result = handle_chat_message(current_user(), session_id, message)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    session["chat_session_id"] = result["session_id"]
    return jsonify(result)


@chatbot_bp.route("/suggestions", methods=["GET"])
def suggestions():
    return jsonify({"suggestions": get_quick_suggestions()})
