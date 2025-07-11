import uuid
from functools import wraps

from flask import g, jsonify, request

from auth.auth import with_auth, workos_client
from models import Database, Organisation, User


def user_middleware(f):
    @wraps(f)
    @with_auth
    def decorated_function(*args, **kwargs):
        # Get or create user based on authentication
        user = g.session.query(User).filter(User.id == g.user.id).first()
        if not user:
            # Create new user from authentication
            user = User(
                id=g.user.id,
                email=g.user.email,
            )
            g.session.add(user)
            g.session.flush()

        g.user = user

        if g.organization_id:
            organisation = (
                g.session.query(Organisation)
                .filter(Organisation.id == g.organization_id)
                .first()
            )
            if not organisation:
                # Create new organization from authentication
                workos_organization = workos_client.organizations.get_organization(
                    organization_id=g.organization_id
                )
                new_organisation = Organisation(
                    id=g.organization_id,
                    name=workos_organization.name,
                )
                g.session.add(new_organisation)
                g.session.flush()
                g.organisation = new_organisation
            else:
                g.organisation = organisation
        else:
            g.organisation = None
        return f(*args, **kwargs)

    return decorated_function


def database_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        database_id = request.json.get("databaseId")
        if isinstance(database_id, str):
            try:
                database_id = uuid.UUID(database_id)
            except ValueError:
                return jsonify({"error": "Invalid databaseId"}), 400
        database = g.session.query(Database).filter_by(id=database_id).first()
        g.data_warehouse = database.create_data_warehouse()
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """Check if user is attached to an organization,
        that is has admin role
        Otherwise, we consider the user is admin
        """
        if g.organization_id is not None and g.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated_function
