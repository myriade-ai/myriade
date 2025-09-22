import uuid
from functools import wraps

from flask import g, jsonify, request

from auth.auth import with_auth
from auth.infra_utils import get_organization_data
from models import Database, Organisation, Project, Query, User


def user_middleware(f):
    @wraps(f)
    @with_auth
    def decorated_function(*args, **kwargs):
        # Get or create user based on authentication
        user = g.session.query(User).filter(User.id == g.auth_user.user.id).first()
        if not user:
            # Create new user from authentication
            user = User(
                id=g.auth_user.user.id,
                email=g.auth_user.user.email,
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

                auth_organization = get_organization_data(g.organization_id)
                new_organisation = Organisation(
                    id=g.organization_id,
                    name=auth_organization["name"],
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
        if not database:
            return jsonify({"error": "Database not found"}), 404

        # Verify user has access to this database
        if (
            database.ownerId != g.user.id
            and database.organisationId != g.organization_id
            and not database.public
        ):
            return jsonify({"error": "Access denied"}), 403

        g.database = database
        g.data_warehouse = database.create_data_warehouse()
        return f(*args, **kwargs)

    return decorated_function


def query_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract query_id from URL parameters
        query_id = kwargs.get("query_id")
        if not query_id:
            return jsonify({"error": "Query ID required"}), 400

        query = g.session.query(Query).filter_by(id=query_id).first()
        if not query:
            return jsonify({"error": "Query not found"}), 404

        # Get the database this query belongs to
        database = g.session.query(Database).filter_by(id=query.databaseId).first()
        if not database:
            return jsonify({"error": "Database not found"}), 404

        # Verify user has access to this database
        if (
            database.ownerId != g.user.id
            and database.organisationId != g.organization_id
            and not database.public
        ):
            return jsonify({"error": "Access denied"}), 403

        g.query = query
        g.database = database
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """Check if user is attached to an organization,
        that is has admin role
        Otherwise, we consider the user is admin
        """
        if g.organization_id is not None and g.auth_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated_function


def extract_context(session, context_id: str) -> tuple[uuid.UUID, uuid.UUID | None]:
    """
    Extract the databaseId from the context_id
    context is "project-{projectId}" or "database-{databaseId}"
    """
    if context_id.startswith("project-"):
        project_id = context_id.removeprefix("project-")
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            raise ValueError(f"Project with id {project_id} not found")
        return project.databaseId, project.id
    elif context_id.startswith("database-"):
        database_id = context_id.removeprefix("database-")
        return uuid.UUID(database_id), None
    else:
        raise ValueError(f"Invalid context_id: {context_id}")


def context_middleware(f):
    """
    Middleware to handle context extraction and database access validation.
    
    This decorator:
    1. Extracts context_id from request (query params or JSON body)
    2. Parses context to get database_id and project_id
    3. Validates user access to the database
    4. Sets up g.database, g.data_warehouse, and g.project (if applicable)
    
    Requires @user_middleware to be applied first.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get context_id from request args or JSON body
        context_id = request.args.get("contextId")
        if not context_id and request.json:
            context_id = request.json.get("contextId")
        
        if not context_id:
            return jsonify({"error": "contextId is required"}), 400
        
        try:
            # Extract database_id and project_id from context
            database_id, project_id = extract_context(g.session, context_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
        # Fetch and validate database access
        database = g.session.query(Database).filter_by(id=database_id).first()
        if not database:
            return jsonify({"error": "Database not found"}), 404
        
        # Verify user has access to this database
        if (
            database.ownerId != g.user.id
            and database.organisationId != g.organization_id
            and not database.public
        ):
            return jsonify({"error": "Access denied"}), 403
        
        # Set up database context
        g.database = database
        g.data_warehouse = database.create_data_warehouse()
        
        # Set up project context if applicable
        if project_id:
            project = g.session.query(Project).filter_by(id=project_id).first()
            if not project:
                return jsonify({"error": "Project not found"}), 404
            g.project = project
        else:
            g.project = None
        
        return f(*args, **kwargs)
    
    return decorated_function
