import logging

from flask import Blueprint, jsonify

from auth.infra_utils import make_authenticated_proxy_request
from config import HOST
from middleware import user_middleware

api = Blueprint("billing_api", __name__)
logger = logging.getLogger(__name__)


@api.route("/billing/create-checkout-session", methods=["POST"])
@user_middleware
def create_checkout_session():
    """Get link to checkout session"""
    response = make_authenticated_proxy_request(
        "/billing/create-checkout-session",
        method="POST",
        timeout=5,
        json={
            "success_url": HOST,
            "cancel_url": HOST,
        },
    )
    response.raise_for_status()
    return jsonify({"url": response.json()["url"]})
