import logging

from flask import Blueprint, jsonify, request

from auth.infra_utils import make_authenticated_proxy_request
from config import HOST
from middleware import user_middleware

api = Blueprint("billing_api", __name__)
logger = logging.getLogger(__name__)


@api.route("/billing/create-checkout-session", methods=["POST"])
@user_middleware
def create_checkout_session():
    """Get link to checkout session"""
    callback_host = HOST if HOST else request.url_root.rstrip("/")
    response = make_authenticated_proxy_request(
        "/billing/create-checkout-session",
        method="POST",
        timeout=5,
        json={
            "success_url": callback_host,
            "cancel_url": callback_host,
        },
    )
    response.raise_for_status()
    return jsonify({"url": response.json()["url"]})
