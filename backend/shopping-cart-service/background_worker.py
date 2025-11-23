import json
import logging
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle_send_order_email(payload: Dict[str, Any]) -> None:
    """
    Mock sending an order confirmation email.
    """
    order_id = payload.get("orderId")
    user_id = payload.get("userId")
    total_amount = payload.get("totalAmount")
    logger.info(
        "Sending order confirmation email (mock)",
        extra={
            "orderId": order_id,
            "userId": user_id,
            "totalAmount": total_amount,
        },
    )


def dispatch_task(message: Dict[str, Any]) -> None:
    task_type = message.get("taskType")
    payload = message.get("payload", {})

    if task_type == "SEND_ORDER_EMAIL":
        handle_send_order_email(payload)
    else:
        logger.warning("Unknown task type", extra={"taskType": task_type})


def lambda_handler(event, context):
    """
    SQS-triggered worker that processes background tasks.
    """
    records = event.get("Records", [])
    for record in records:
        body = record.get("body") or "{}"
        message = json.loads(body)
        dispatch_task(message)
