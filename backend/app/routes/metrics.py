"""Metrics routes with improved error handling and validation."""

from flask import Blueprint, request

from app.models import Device, Metric
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
    """Submit new metrics for a device.
    ---
    tags:
      - Metrics
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - device_id
          properties:
            device_id:
              type: integer
              description: ID of the device
              example: 1
            cpu_usage:
              type: number
              format: float
              description: CPU usage percentage (0-100)
              example: 45.2
            memory_usage:
              type: number
              format: float
              description: Memory usage percentage (0-100)
              example: 67.8
            disk_usage:
              type: number
              format: float
              description: Disk usage percentage (0-100)
              example: 82.1
            network_rx_bytes:
              type: integer
              description: Network received bytes
              example: 1048576
            network_tx_bytes:
              type: integer
              description: Network transmitted bytes
              example: 524288
    responses:
      201:
        description: Metrics submitted successfully
        schema:
          type: object
          properties:
            data:
              $ref: '#/definitions/Metric'
      400:
        description: Validation error
      404:
        description: Device not found
    """
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
