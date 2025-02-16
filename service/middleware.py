from functools import wraps

from flask import g, jsonify, request

from back.datalake import DatalakeFactory
from back.models import Database, User
from middlewares.clerk import clerk_middleware


def user_middleware(f):
    @clerk_middleware
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get or create user based on Clerk authentication
        user = g.session.query(User).filter(User.id == g.user_id).first()
        if not user:
            # Create new user from Clerk data
            user = User(
                id=g.user_id,
                email=g.user_email,
            )
            g.session.add(user)
            g.session.commit()

        g.user = user
        return f(*args, **kwargs)

    return decorated_function


def database_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        database_id = request.json.get("databaseId")
        database = g.session.query(Database).filter_by(id=database_id).first()
        # Add a datalake object to the request
        datalake = DatalakeFactory.create(
            database.engine,
            **database.details,
        )
        datalake.privacy_mode = database.privacy_mode
        datalake.safe_mode = database.safe_mode
        g.datalake = datalake
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, "user") or not g.user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated_function
