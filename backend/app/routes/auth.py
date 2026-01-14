"""Authentication routes."""

from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

from app.extensions import limiter
from app.models import User
from app.schemas.auth import LoginRequest, PasswordChange, UserCreate, UserUpdate
from app.utils.audit import log_login_failure, log_login_success
from app.utils.errors import (
    ConflictError,
    DatabaseSession,
    NotFoundError,
    ValidationError,
    success_response,
)
from app.utils.validation import validate_request

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
@validate_request(LoginRequest)
def login():
    """Authenticate user and return JWT token.
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: Username
              example: admin
            password:
              type: string
              description: Password
              example: SecurePass123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            access_token:
              type: string
              description: JWT access token
            token_type:
              type: string
              example: bearer
      401:
        description: Invalid credentials
    """
    data = request.validated_data

    with DatabaseSession() as db:
        user = db.query(User).filter(User.username == data.username.lower()).first()

        if not user or not user.check_password(data.password):
            log_login_failure(data.username, "invalid_credentials")
            raise ValidationError("Invalid username or password")

        if not user.is_active:
            log_login_failure(data.username, "account_disabled")
            raise ValidationError("Account is disabled")

        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)

        # Log successful login
        log_login_success(user.id, user.username)

        # Create access token with user ID as identity (must be string for JWT)
        access_token = create_access_token(identity=str(user.id))

        return success_response({
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_dict(include_email=True),
        })


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get current authenticated user.
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Current user info
        schema:
          $ref: '#/definitions/User'
      401:
        description: Not authenticated
    """
    user_id = int(get_jwt_identity())

    with DatabaseSession() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)

        return success_response(user.to_dict(include_email=True))


@auth_bp.route("/me", methods=["PUT"])
@jwt_required()
@validate_request(UserUpdate)
def update_current_user():
    """Update current user profile.
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              format: email
            display_name:
              type: string
            avatar_url:
              type: string
            bio:
              type: string
    responses:
      200:
        description: User updated
      401:
        description: Not authenticated
    """
    user_id = int(get_jwt_identity())
    data = request.validated_data

    with DatabaseSession() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)

        # Update allowed fields (non-admin can't change is_admin or is_active)
        if data.email is not None:
            # Check email uniqueness
            existing = db.query(User).filter(
                User.email == data.email, User.id != user_id
            ).first()
            if existing:
                raise ConflictError("Email already in use")
            user.email = data.email
        if data.display_name is not None:
            user.display_name = data.display_name
        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url
        if data.bio is not None:
            user.bio = data.bio

        db.commit()
        db.refresh(user)

        return success_response(user.to_dict(include_email=True))


@auth_bp.route("/me/password", methods=["PUT"])
@jwt_required()
@validate_request(PasswordChange)
def change_password():
    """Change current user's password.
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - current_password
            - new_password
          properties:
            current_password:
              type: string
            new_password:
              type: string
    responses:
      200:
        description: Password changed
      400:
        description: Current password incorrect
      401:
        description: Not authenticated
    """
    user_id = int(get_jwt_identity())
    data = request.validated_data

    with DatabaseSession() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)

        if not user.check_password(data.current_password):
            raise ValidationError("Current password is incorrect")

        user.set_password(data.new_password)
        db.commit()

        return success_response(message="Password changed successfully")


# Admin-only user management routes
@auth_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    """List all users (admin only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: List of users
        schema:
          type: array
          items:
            $ref: '#/definitions/User'
      401:
        description: Not authenticated
      403:
        description: Admin access required
    """
    user_id = int(get_jwt_identity())

    with DatabaseSession() as db:
        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user or not current_user.is_admin:
            raise ValidationError("Admin access required")

        users = db.query(User).all()
        return success_response([user.to_dict(include_email=True) for user in users])


@auth_bp.route("/users", methods=["POST"])
@jwt_required()
@validate_request(UserCreate)
def create_user():
    """Create a new user (admin only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              minLength: 3
              maxLength: 80
            email:
              type: string
              format: email
            password:
              type: string
              minLength: 8
            display_name:
              type: string
            is_admin:
              type: boolean
    responses:
      201:
        description: User created
      400:
        description: Validation error
      401:
        description: Not authenticated
      403:
        description: Admin access required
      409:
        description: User already exists
    """
    admin_id = int(get_jwt_identity())
    data = request.validated_data

    with DatabaseSession() as db:
        current_user = db.query(User).filter(User.id == admin_id).first()
        if not current_user or not current_user.is_admin:
            raise ValidationError("Admin access required")

        # Check for existing username
        if db.query(User).filter(User.username == data.username).first():
            raise ConflictError("Username already exists")

        # Check for existing email
        if db.query(User).filter(User.email == data.email).first():
            raise ConflictError("Email already in use")

        user = User(
            username=data.username,
            email=data.email,
            display_name=data.display_name,
            is_admin=data.is_admin,
        )
        user.set_password(data.password)

        db.add(user)
        db.commit()
        db.refresh(user)

        return success_response(user.to_dict(include_email=True), status_code=201)


@auth_bp.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id: int):
    """Get a specific user (admin only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: User details
      401:
        description: Not authenticated
      403:
        description: Admin access required
      404:
        description: User not found
    """
    admin_id = int(get_jwt_identity())

    with DatabaseSession() as db:
        current_user = db.query(User).filter(User.id == admin_id).first()
        if not current_user or not current_user.is_admin:
            raise ValidationError("Admin access required")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)

        return success_response(user.to_dict(include_email=True))


@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
@jwt_required()
@validate_request(UserUpdate)
def update_user(user_id: int):
    """Update a user (admin only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              format: email
            display_name:
              type: string
            is_admin:
              type: boolean
            is_active:
              type: boolean
    responses:
      200:
        description: User updated
      401:
        description: Not authenticated
      403:
        description: Admin access required
      404:
        description: User not found
    """
    admin_id = int(get_jwt_identity())
    data = request.validated_data

    with DatabaseSession() as db:
        current_user = db.query(User).filter(User.id == admin_id).first()
        if not current_user or not current_user.is_admin:
            raise ValidationError("Admin access required")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)

        # Update fields
        if data.email is not None:
            existing = db.query(User).filter(
                User.email == data.email, User.id != user_id
            ).first()
            if existing:
                raise ConflictError("Email already in use")
            user.email = data.email
        if data.display_name is not None:
            user.display_name = data.display_name
        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url
        if data.bio is not None:
            user.bio = data.bio
        if data.is_admin is not None:
            # Prevent removing own admin status
            if user_id == admin_id and not data.is_admin:
                raise ValidationError("Cannot remove your own admin status")
            user.is_admin = data.is_admin
        if data.is_active is not None:
            # Prevent deactivating yourself
            if user_id == admin_id and not data.is_active:
                raise ValidationError("Cannot deactivate your own account")
            user.is_active = data.is_active

        db.commit()
        db.refresh(user)

        return success_response(user.to_dict(include_email=True))


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id: int):
    """Delete a user (admin only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: User deleted
      401:
        description: Not authenticated
      403:
        description: Admin access required
      404:
        description: User not found
    """
    admin_id = int(get_jwt_identity())

    with DatabaseSession() as db:
        current_user = db.query(User).filter(User.id == admin_id).first()
        if not current_user or not current_user.is_admin:
            raise ValidationError("Admin access required")

        if user_id == admin_id:
            raise ValidationError("Cannot delete your own account")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)

        db.delete(user)
        db.commit()

        return success_response(message="User deleted successfully")


@auth_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@jwt_required()
@validate_request(PasswordChange)
def admin_reset_password(user_id: int):
    """Reset a user's password (admin only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - new_password
          properties:
            new_password:
              type: string
              minLength: 8
    responses:
      200:
        description: Password reset
      401:
        description: Not authenticated
      403:
        description: Admin access required
      404:
        description: User not found
    """
    admin_id = int(get_jwt_identity())

    with DatabaseSession() as db:
        current_user = db.query(User).filter(User.id == admin_id).first()
        if not current_user or not current_user.is_admin:
            raise ValidationError("Admin access required")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)

        # Get new password from request body
        data = request.get_json()
        new_password = data.get("new_password")
        if not new_password or len(new_password) < 8:
            raise ValidationError("New password must be at least 8 characters")

        user.set_password(new_password)
        db.commit()

        return success_response(message="Password reset successfully")
