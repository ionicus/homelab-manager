"""Authentication routes."""

from datetime import datetime
from io import BytesIO

from flask import Blueprint, Response, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from PIL import Image

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


# Allowed MIME types for avatar uploads
ALLOWED_AVATAR_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB
AVATAR_MAX_DIMENSION = 256  # Max width/height for avatars


def process_avatar_image(file_data: bytes) -> tuple[bytes, str]:
    """Process and optimize avatar image.

    Resizes to max 256x256 while preserving aspect ratio,
    converts to PNG for consistency, and optimizes file size.

    Returns:
        Tuple of (processed_image_bytes, mime_type)
    """
    img = Image.open(BytesIO(file_data))

    # Handle different image modes
    if img.mode in ("RGBA", "LA", "P"):
        # Keep alpha channel for transparency
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # Resize if larger than max dimension
    if img.width > AVATAR_MAX_DIMENSION or img.height > AVATAR_MAX_DIMENSION:
        img.thumbnail((AVATAR_MAX_DIMENSION, AVATAR_MAX_DIMENSION), Image.Resampling.LANCZOS)

    # Save as PNG with optimization
    output = BytesIO()
    img.save(output, format="PNG", optimize=True)

    return output.getvalue(), "image/png"


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
            # Clear uploaded avatar when setting external URL
            if data.avatar_url:
                user.avatar_data = None
                user.avatar_mime_type = None
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


@auth_bp.route("/me/avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    """Upload avatar image for current user (stored in database).
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - name: avatar
        in: formData
        type: file
        required: true
        description: Avatar image file (PNG, JPG, GIF, WebP, max 5MB)
    responses:
      200:
        description: Avatar uploaded successfully
        schema:
          type: object
          properties:
            avatar_url:
              type: string
              description: URL to the uploaded avatar
      400:
        description: Invalid file or no file provided
      401:
        description: Not authenticated
    """
    user_id = int(get_jwt_identity())

    if "avatar" not in request.files:
        raise ValidationError("No avatar file provided")

    file = request.files["avatar"]
    if file.filename == "":
        raise ValidationError("No file selected")

    # Validate MIME type
    mime_type = file.content_type
    if mime_type not in ALLOWED_AVATAR_MIME_TYPES:
        raise ValidationError("Invalid file type. Allowed: PNG, JPG, GIF, WebP")

    # Read file data
    file_data = file.read()

    # Validate file size
    if len(file_data) > MAX_AVATAR_SIZE:
        raise ValidationError("File too large. Maximum size is 5MB")

    # Process image: resize and optimize
    try:
        processed_data, processed_mime = process_avatar_image(file_data)
    except Exception:
        raise ValidationError("Invalid image file")

    with DatabaseSession() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)

        # Store processed avatar in database
        user.avatar_data = processed_data
        user.avatar_mime_type = processed_mime
        user.avatar_url = None  # Clear external URL when uploading

        db.commit()
        db.refresh(user)

        return success_response({
            "avatar_url": f"/api/auth/users/{user_id}/avatar",
            "user": user.to_dict(include_email=True),
        })


@auth_bp.route("/me/avatar", methods=["DELETE"])
@jwt_required()
def delete_avatar():
    """Delete avatar for current user.
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Avatar deleted successfully
      401:
        description: Not authenticated
    """
    user_id = int(get_jwt_identity())

    with DatabaseSession() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)

        # Clear both uploaded and external avatar
        user.avatar_data = None
        user.avatar_mime_type = None
        user.avatar_url = None

        db.commit()
        db.refresh(user)

        return success_response({
            "message": "Avatar deleted successfully",
            "user": user.to_dict(include_email=True),
        })


@auth_bp.route("/users/<int:user_id>/avatar", methods=["GET"])
def get_user_avatar(user_id: int):
    """Get user's avatar image.
    ---
    tags:
      - Users
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Avatar image
      404:
        description: User or avatar not found
    """
    with DatabaseSession() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User", user_id)

        if not user.avatar_data:
            raise NotFoundError("Avatar", user_id)

        return Response(
            user.avatar_data,
            mimetype=user.avatar_mime_type or "image/png",
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 1 day
            },
        )


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
