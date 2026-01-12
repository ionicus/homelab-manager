"""Metrics routes with improved error handling and validation."""

from flask import Blueprint, request

from app.models import Metric, Device
from app.schemas.metric import MetricCreate
from app.utils.errors import (
    DatabaseSession,
    NotFoundError,
    success_response,
)
from app.utils.validation import validate_request

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("", methods=["POST"])
@validate_request(MetricCreate)
def submit_metrics():
    """Submit new metrics."""
    data = request.validated_data

    with DatabaseSession() as db:
        # Verify device exists
        device = db.query(Device).filter(Device.id == data.device_id).first()
        if not device:
            raise NotFoundError("Device", data.device_id)

        metric = Metric(
            device_id=data.device_id,
            cpu_usage=data.cpu_usage,
            memory_usage=data.memory_usage,
            disk_usage=data.disk_usage,
            network_rx_bytes=data.network_rx_bytes,
            network_tx_bytes=data.network_tx_bytes,
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        return success_response(metric.to_dict(), status_code=201)
