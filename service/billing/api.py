import json
import logging

import stripe
from flask import Blueprint, g, jsonify, request

import config
from middleware import user_middleware
from models import User

stripe.api_key = config.STRIPE_SECRET_KEY

api = Blueprint("billing_api", __name__)
logger = logging.getLogger(__name__)


@api.route("/create-checkout-session", methods=["POST"])
@user_middleware
def create_checkout_session():
    subscription_url = request.referrer
    scheme = "https" if config.ENV == "production" else "http"
    host_url = scheme + "://" + config.HOST
    prices = stripe.Price.list(
        lookup_keys=["standard_monthly"],
        expand=["data.product"],
    )

    if not prices.data:
        logger.error("No prices found with lookup_key 'standard_monthly'")
        return jsonify({"error": "Product price not found"}), 400

    price_id = prices.data[0].id

    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            },
        ],
        mode="subscription",
        customer_email=g.user.email,
        success_url=host_url,
        cancel_url=subscription_url,
    )
    return jsonify({"url": checkout_session.url})


@api.route("/webhook/stripe", methods=["POST"])
def webhook_received():
    # TODO: add webhook secret
    request_data = json.loads(request.data)
    event_type = request_data["type"]
    event = request_data["data"]["object"]

    print("event " + event_type)

    if event_type == "checkout.session.completed":
        print("🔔 Payment succeeded!")
        g.session.query(User).filter_by(email=event["customer_email"]).update(
            {"has_active_subscription": True}
        )
        g.session.flush()
    elif event_type == "customer.subscription.trial_will_end":
        print("Subscription trial will end")
    elif event_type == "customer.subscription.created":
        print("Subscription created %s", event["id"])
    elif event_type == "customer.subscription.updated":
        print("Subscription created %s", event["id"])
    elif event_type == "customer.subscription.deleted":
        # handle subscription canceled automatically based
        # upon your subscription settings. Or if the user cancels it.
        print("Subscription canceled: %s", event["id"])
    elif event_type == "entitlements.active_entitlement_summary.updated":
        # handle active entitlement summary updated
        print("Active entitlement summary updated: %s", event["id"])

    return jsonify({"status": "success"})
