"""Metrics routes."""

from flask import Blueprint, request, jsonify

from app.database import Session
from app.models import Metric, Device

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("", methods=["POST"])
def submit_metrics():
    """Submit new metrics."""
    data = request.get_json()

    if not data or "device_id" not in data:
        return jsonify({"error": "Missing required field: device_id"}), 400

    db = Session()
    try:
        # Verify device exists
        device = db.query(Device).filter(Device.id == data["device_id"]).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        metric = Metric(
            device_id=data["device_id"],
            cpu_usage=data.get("cpu_usage"),
            memory_usage=data.get("memory_usage"),
            disk_usage=data.get("disk_usage"),
            network_rx_bytes=data.get("network_rx_bytes"),
            network_tx_bytes=data.get("network_tx_bytes"),
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        return jsonify(metric.to_dict()), 201
    finally:
        db.close()
