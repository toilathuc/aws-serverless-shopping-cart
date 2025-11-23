import os

import requests
from aws_lambda_powertools import Logger, Tracer

from shared import NotFoundException

product_service_url = os.environ["PRODUCT_SERVICE_URL"]

logger = Logger()
tracer = Tracer()


@tracer.capture_method
def get_product_from_external_service(product_id):
    """
    Call product API to retrieve product details
    """
    try:
        response = requests.get(
            product_service_url + f"/product/{product_id}", timeout=5
        )
    except requests.RequestException as exc:
        logger.exception(
            "Failed to call product service",
            extra={"product_id": product_id, "url": product_service_url, "error": str(exc)},
        )
        raise NotFoundException

    if response.status_code != 200:
        logger.warning(
            "Product service returned non-200",
            extra={
                "product_id": product_id,
                "url": product_service_url,
                "status": response.status_code,
                "body": response.text[:512],
            },
        )
        raise NotFoundException

    try:
        response_dict = response.json()["product"]
    except (ValueError, KeyError) as exc:
        logger.warning(
            "Unexpected response from product service",
            extra={
                "product_id": product_id,
                "url": product_service_url,
                "status": response.status_code,
                "body": response.text[:512],
                "error": str(exc),
            },
        )
        raise NotFoundException

    return response_dict
