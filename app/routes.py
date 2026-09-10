from flask import Blueprint, jsonify

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return "BetAggregator is running"


@main_bp.get("/health")
def health():
    return jsonify({"status": "ok"})
