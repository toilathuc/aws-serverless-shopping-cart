import os
from collections import Counter
from datetime import datetime, timezone

import boto3
from aws_lambda_powertools import Logger, Tracer
from boto3.dynamodb import types

logger = Logger()
tracer = Tracer()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
agg_table_name = os.environ.get("AGG_TABLE_NAME")
agg_table = dynamodb.Table(agg_table_name) if agg_table_name else None
AGGREGATE_PK = os.environ.get("AGGREGATE_PK", "STATS")

deserializer = types.TypeDeserializer()


@tracer.capture_method
def dynamodb_to_python(dynamodb_item):
    """
    Convert from dynamodb low level format to python dict
    """
    return {k: deserializer.deserialize(v) for k, v in dynamodb_item.items()}


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """
    Handle streams from DynamoDB table
    """

    records = event["Records"]
    quantity_change_counter = Counter()

    for record in records:
        keys = dynamodb_to_python(record["dynamodb"]["Keys"])
        sk = keys.get("sk", "")
        # NewImage record only exists if the event is INSERT or MODIFY
        new_image = dynamodb_to_python(record["dynamodb"].get("NewImage", {}))

        old_image_ddb = record["dynamodb"].get("OldImage")

        if old_image_ddb:
            old_image = dynamodb_to_python(
                record["dynamodb"].get("OldImage")
            )  # Won't exist in case event is INSERT
        else:
            old_image = {}

        # We want to record the quantity change the change made to the db rather than absolute values
        if sk.startswith("product#"):
            delta = new_image.get("quantity", 0) - old_image.get("quantity", 0)
            if delta != 0:
                product_id = sk.replace("product#", "")
                quantity_change_counter.update({product_id: delta})

    now_iso = datetime.now(timezone.utc).isoformat()

    for product_id, delta in quantity_change_counter.items():
        logger.info(
            "Updating aggregate totals",
            extra={"product_id": product_id, "delta": delta},
        )
        target_table = agg_table or table
        target_table.update_item(
            Key={"pk": AGGREGATE_PK},
            ExpressionAttributeNames={
                "#productTotals": "productTotals",
                "#pid": product_id,
                "#totalItems": "totalItems",
                "#updatedAt": "updatedAt",
            },
            ExpressionAttributeValues={
                ":delta": delta,
                ":empty": {},
                ":zero": 0,
                ":updatedAt": now_iso,
            },
            UpdateExpression=(
                "SET #productTotals = if_not_exists(#productTotals, :empty), "
                "#totalItems = if_not_exists(#totalItems, :zero), "
                "#updatedAt = :updatedAt "
                "ADD #productTotals.#pid :delta, #totalItems :delta"
            ),
        )

    return {
        "statusCode": 200,
    }
