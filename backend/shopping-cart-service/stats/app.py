"""Admin statistics API Lambda."""

import json
import os

import boto3
from aws_lambda_powertools import Logger, Tracer
from botocore.exceptions import ClientError

from shared import HEADERS, handle_decimal_type

logger = Logger()
tracer = Tracer()

dynamodb = boto3.resource("dynamodb")
aggregate_table = dynamodb.Table(os.environ["AGG_TABLE_NAME"])

AGGREGATE_PK = os.environ.get("AGGREGATE_PK", "STATS")
ADMIN_GROUP = os.environ.get("ADMIN_GROUP", "admin")


def _user_is_admin(event):
    """Return True when Cognito claims contain the configured admin group."""

    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("claims", {})
    )
    groups_raw = claims.get("cognito:groups", "")

    if isinstance(groups_raw, str):
        groups = [group.strip() for group in groups_raw.split(",") if group.strip()]
    elif isinstance(groups_raw, list):
        groups = groups_raw
    else:
        groups = []

    return ADMIN_GROUP in groups


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    headers = dict(HEADERS)
    headers["Content-Type"] = "application/json"

    if not _user_is_admin(event):
        return {
            "statusCode": 403,
            "headers": headers,
            "body": json.dumps({"message": "Forbidden"}),
        }

    try:
        response = aggregate_table.get_item(Key={"pk": AGGREGATE_PK})
    except ClientError as exc:
        logger.exception("Failed to load stats", extra={"error": exc.response["Error"]})
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"message": "Failed to load stats"}),
        }

    stats = response.get("Item", {"pk": AGGREGATE_PK})

    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps(stats, default=handle_decimal_type),
    }
